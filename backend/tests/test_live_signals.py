"""Deterministic transport tests: no public-network predictions or timings asserted."""
import asyncio
import pytest
from fastapi.testclient import TestClient
from backend.app.main import create_app
from backend.app import live_signals as live


@pytest.mark.parametrize('address', ['127.0.0.1','10.0.0.1','169.254.169.254','::1','::ffff:8.8.8.8','224.0.0.1','192.0.2.1','64:ff9b::7f00:1','2002:7f00:1::'])
def test_non_public_destinations_blocked(address):
    with pytest.raises(live.BlockedTarget):
        live.public_address(address)


@pytest.mark.parametrize('url', ['http://127.0.0.1/', 'https://user:pass@example.com/', 'https://example.com:8443/'])
def test_target_policy(url):
    with pytest.raises(live.BlockedTarget):
        live.target(url)


def test_dns_rejects_mixed_public_private_answers(monkeypatch):
    async def run():
        async def answers(*args, **kwargs):
            return [(2,1,6,'',('8.8.8.8',443)), (2,1,6,'',('127.0.0.1',443))]
        monkeypatch.setattr(asyncio.get_running_loop(), 'getaddrinfo', answers)
        with pytest.raises(live.BlockedTarget):
            await live.resolve('example.com',443)
    asyncio.run(run())


def test_private_redirect_never_connected(monkeypatch):
    requests = []
    async def resolve(host, port):
        return ['8.8.8.8']
    async def request(parsed, *args):
        requests.append(parsed.ascii_host)
        return 302, 'http://127.0.0.1/secret', None
    async def age(parsed):
        return live.observation('Domain age', 'unavailable')
    monkeypatch.setattr(live, 'resolve', resolve)
    monkeypatch.setattr(live, 'request_pinned', request)
    monkeypatch.setattr(live, 'domain_age', age)
    result = asyncio.run(live.collect('https://example.com/'))
    assert requests == ['example.com']
    assert result['checks'][2]['status'] == 'blocked'
    assert result['affects_model_score'] is False


def test_tls_failure_does_not_claim_validity(monkeypatch):
    async def probe(*args, **kwargs):
        raise OSError('certificate verification failed')
    monkeypatch.setattr(live, 'probe', probe)
    result = asyncio.run(live.collect('https://example.com/'))
    assert all(c['status'] == 'unavailable' for c in result['checks'])


def test_registration_requires_matching_domain(monkeypatch):
    async def probe(*args, **kwargs):
        return None, [], 200, None, {'ldhName':'other.com','events':[{'eventAction':'registration','eventDate':'2000-01-01T00:00:00Z'}]}
    monkeypatch.setattr(live, 'probe', probe)
    result = asyncio.run(live.domain_age(live.target('https://example.com/')[0]))
    assert result['status'] == 'unavailable'


def test_live_checks_opt_in_and_fixture_never_fetches(monkeypatch):
    monkeypatch.delenv('PHISHX_LIVE_SIGNALS', raising=False)
    with TestClient(create_app(mode='model')) as client:
        assert client.post('/signals',json={'url':'https://example.com/'}).status_code == 503
    monkeypatch.setenv('PHISHX_LIVE_SIGNALS','1')
    with TestClient(create_app(mode='fixture')) as client:
        assert client.post('/signals',json={'url':'https://example.com/'}).status_code == 503
    with TestClient(create_app(mode='model')) as client:
        assert client.post('/signals',json={'url':'http://127.0.0.1/'}).status_code == 422


def test_redirect_limit_is_not_presented_as_complete(monkeypatch):
    async def probe(url, **kwargs):
        return live.target(url)[0], ['8.8.8.8'], 302, '/again', None
    monkeypatch.setattr(live, 'probe', probe)
    result = asyncio.run(live.collect('https://example.com/'))
    assert len(result['redirect_chain']) == 4
    assert result['checks'][2]['status'] == 'unavailable'


def test_total_timeout_and_busy_responses(monkeypatch):
    monkeypatch.setenv('PHISHX_LIVE_SIGNALS', '1')
    async def timeout(url):
        raise TimeoutError()
    monkeypatch.setattr(live, 'collect', timeout)
    with TestClient(create_app(mode='model')) as client:
        assert client.post('/signals',json={'url':'https://example.com/'}).status_code == 504
        class Busy:
            async def acquire(self):
                raise TimeoutError()
        client.app.state.live_slots = Busy()
        assert client.post('/signals',json={'url':'https://example.com/'}).status_code == 429


def test_pinned_transport_uses_ip_and_original_tls_hostname(monkeypatch):
    async def run():
        reader = asyncio.StreamReader()
        reader.feed_data(b'HTTP/1.1 200 OK\r\nContent-Length: 999999\r\n\r\n')
        reader.feed_eof()
        class Writer:
            def write(self, data):
                assert b'Host: example.com\r\n' in data
                assert data.startswith(b'HEAD / HTTP/1.1')
            async def drain(self): pass
            def close(self): pass
        async def connect(address, port, **kwargs):
            assert address == '8.8.8.8'
            assert kwargs['server_hostname'] == 'example.com'
            assert kwargs['ssl'].check_hostname
            return reader, Writer()
        monkeypatch.setattr(asyncio, 'open_connection', connect)
        result = await live.request_pinned(live.target('https://example.com/')[0],443,'8.8.8.8')
        assert result == (200, None, None)
    asyncio.run(run())


def test_live_response_contract(monkeypatch):
    monkeypatch.setenv('PHISHX_LIVE_SIGNALS','1')
    async def collect(url):
        # Transport fixture only; not recorded as a measured live observation.
        return {'checks':[live.observation('TLS validity','available',True)], 'redirect_chain':[{'scheme':'https','host':'example.com','http_status':200}], 'checked_at':'2026-10-21T00:00:00+00:00','affects_model_score':False}
    monkeypatch.setattr(live,'collect',collect)
    with TestClient(create_app(mode='model')) as client:
        response = client.post('/signals',json={'url':'https://example.com/'})
        assert response.status_code == 200
        assert response.json()['checks'][0]['value'] is True
        assert response.json()['affects_model_score'] is False
