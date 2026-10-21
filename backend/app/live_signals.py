"""Opt-in observations; never feed these values into the frozen text model.

Resolve each hop once, reject every non-public answer, and connect to a pinned
address while verifying TLS against the original hostname. Never read page bodies.
"""
import asyncio
import ipaddress
import json
import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit, quote

from phishx.urls import normalize_url


class BlockedTarget(ValueError):
    pass


def public_address(value):
    address = ipaddress.ip_address(value)
    transitional = isinstance(address, ipaddress.IPv6Address) and (
        address.sixtofour is not None or address.teredo is not None or address.scope_id is not None
        or address in ipaddress.ip_network('64:ff9b::/96')
        or address in ipaddress.ip_network('64:ff9b:1::/48'))
    if not address.is_global or address.is_multicast or getattr(address, 'ipv4_mapped', None) is not None or transitional:
        raise BlockedTarget("Private, reserved and mapped addresses are blocked.")
    return str(address)


async def resolve(host, port):
    answers = await asyncio.wait_for(asyncio.get_running_loop().getaddrinfo(
        host, port, type=socket.SOCK_STREAM), timeout=2)
    addresses = sorted({public_address(answer[4][0]) for answer in answers})
    if not addresses:
        raise OSError("DNS returned no addresses")
    return addresses


def target(url):
    parsed = normalize_url(url)
    port = urlsplit(parsed.canonical).port or (443 if parsed.scheme == 'https' else 80)
    if parsed.has_userinfo or port != (443 if parsed.scheme == 'https' else 80):
        raise BlockedTarget("Credentials and non-standard ports are blocked for live checks.")
    if parsed.is_ip:
        public_address(parsed.ascii_host)
    return parsed, port


async def request_pinned(parsed, port, address, method='HEAD', read_json=False):
    reader, writer = await asyncio.open_connection(
        address, port, ssl=ssl.create_default_context() if parsed.scheme == 'https' else None,
        server_hostname=parsed.ascii_host if parsed.scheme == 'https' else None, limit=65536)
    try:
        path = quote(parsed.path or '/', safe="/%:@!$&'()*+,;=-._~")
        if parsed.query:
            path += '?' + quote(parsed.query, safe="/%?:@!$&'()*+,;=-._~")
        host = '[' + parsed.ascii_host + ']' if ':' in parsed.ascii_host else parsed.ascii_host
        writer.write((f"{method} {path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: PhishX-research/0.2\r\nAccept: application/rdap+json\r\nConnection: close\r\n\r\n").encode('ascii'))
        await writer.drain()
        headers = (await reader.readuntil(b'\r\n\r\n')).decode('iso-8859-1').split('\r\n')
        status = int(headers[0].split()[1])
        fields = {}
        for line in headers[1:]:
            if line:
                key, value = line.split(':', 1)
                fields[key.lower()] = value.strip()
        data = None
        if read_json and status == 200:
            raw = bytearray()
            if fields.get('transfer-encoding', '').lower() == 'chunked':
                while True:
                    size = int((await reader.readline()).split(b';')[0], 16)
                    if not size:
                        break
                    if size < 0 or len(raw) + size > 262144:
                        raise ValueError('RDAP response too large')
                    raw.extend(await reader.readexactly(size))
                    if await reader.readexactly(2) != b'\r\n':
                        raise ValueError('Invalid chunk')
            else:
                while True:
                    chunk = await reader.read(min(16384, 262145-len(raw)))
                    if not chunk:
                        break
                    raw.extend(chunk)
                    if len(raw) > 262144:
                        raise ValueError('RDAP response too large')
            data = json.loads(raw)
        return status, fields.get('location'), data
    finally:
        writer.close()
        # Closing the transport also cancels stalled peers; do not await TLS shutdown.


async def probe(url, *, rdap=False):
    parsed, port = target(url)
    addresses = await resolve(parsed.ascii_host, port)
    status, location, data = await asyncio.wait_for(request_pinned(parsed, port, addresses[0], 'GET' if rdap else 'HEAD', rdap), timeout=4)
    return parsed, addresses, status, location, data


def observation(name, status, value=None, message=None):
    return {'name': name, 'status': status, 'value': value, 'message': message}


async def domain_age(parsed):
    if parsed.is_ip:
        return observation('Domain age', 'unavailable', message='IP addresses have no domain registration age.')
    url = 'https://rdap.org/domain/' + parsed.registrable_domain
    try:
        for _ in range(4):
            current, _, status, location, data = await probe(url, rdap=True)
            if status in {301, 302, 303, 307, 308} and location:
                url = urljoin(current.canonical, location)
                if urlsplit(url).scheme != 'https':
                    raise BlockedTarget('RDAP requires HTTPS')
                continue
            if status != 200 or not isinstance(data, dict):
                break
            # Require the registry response to identify the requested domain.
            if str(data.get('ldhName', '')).lower().rstrip('.') != parsed.registrable_domain:
                break
            for event in data.get('events', []):
                if event.get('eventAction') == 'registration':
                    created = datetime.fromisoformat(event['eventDate'].replace('Z', '+00:00'))
                    days = (datetime.now(timezone.utc) - created).days
                    if days >= 0:
                        return observation('Domain age', 'available', days, 'Days since RDAP registration; registration is not a safety verdict.')
            break
    except (OSError, ValueError, TimeoutError, asyncio.IncompleteReadError, asyncio.LimitOverrunError, TypeError, KeyError, IndexError, AttributeError):
        pass
    return observation('Domain age', 'unavailable', message='Registry registration date unavailable or lookup timed out.')


async def collect(url):
    parsed, _ = target(url)
    checks = []
    chain = []
    current = parsed.canonical
    initial = True
    for hop in range(4):
        try:
            normalized, addresses, status, location, _ = await probe(current)
            if initial:
                checks.append(observation('DNS', 'available', ', '.join(addresses), 'Public DNS answers at lookup time.'))
                checks.append(observation('TLS validity', 'available' if normalized.scheme == 'https' else 'not_applicable', normalized.scheme == 'https', 'HTTPS certificate chain and hostname verified.' if normalized.scheme == 'https' else 'The submitted URL uses HTTP.'))
                initial = False
            chain.append({'scheme': normalized.scheme, 'host': normalized.ascii_host, 'http_status': status})
            if status in {301, 302, 303, 307, 308} and location:
                if hop == 3:
                    checks.append(observation('Redirects', 'unavailable', len(chain)-1, 'Redirect limit reached; chain is incomplete.'))
                    break
                current = urljoin(normalized.canonical, location)
                continue
            checks.append(observation('Redirects', 'available', len(chain)-1, 'HEAD redirect hops observed; servers may treat browser GET requests differently.'))
            break
        except (OSError, ValueError, TimeoutError, asyncio.IncompleteReadError, asyncio.LimitOverrunError, TypeError, KeyError, IndexError, AttributeError) as exc:
            state = 'blocked' if isinstance(exc, BlockedTarget) else 'unavailable'
            if initial:
                checks.extend([observation('DNS', state, message='DNS or initial connection could not complete safely.'), observation('TLS validity', state, message='Certificate validation or connection did not complete.')])
            checks.append(observation('Redirects', state, message='A target was blocked, unreachable, or timed out. No page body was read.'))
            break
    checks.append(await domain_age(parsed))
    return {'checks': checks, 'redirect_chain': chain, 'checked_at': datetime.now(timezone.utc).isoformat(), 'affects_model_score': False}
