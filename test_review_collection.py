"""Navigation-source checks: no phishing-page fetches or empty-page labels."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('collect_review_data',
    Path(__file__).resolve().parents[1] / 'scripts/collect_review_data.py')
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


def test_collection_only_fetches_seed_and_keeps_same_host_navigation(monkeypatch):
    calls = []
    class Response:
        status_code = 200
        url = 'https://docs.example.org/index'
        headers = {'Content-Type': 'text/html'}
        text = '''<title>Reviewed documentation</title>
        <a href="/guide#one">Guide</a><a href="https://attacker.example/">External</a>
        <a href="https://tenant.example.org/login">Different host</a>
        <a href="/guide?token=secret">Query</a><a href="/guide">Duplicate</a>'''
        content = text.encode()
        def raise_for_status(self): pass
    def get(url, **kwargs):
        calls.append(url)
        return Response()
    monkeypatch.setattr(collector.requests, 'get', get)
    result = collector.collect_one('https://docs.example.org/index')
    assert calls == ['https://docs.example.org/index']
    assert set(result['urls']) == {'https://docs.example.org/index','https://docs.example.org/guide'}


def test_empty_challenge_page_is_not_labeled_benign(monkeypatch):
    class Empty:
        status_code = 202
        url = 'https://docs.example.org/index'
        headers = {'Content-Type': 'text/html'}
        text = ''; content = b''
        def raise_for_status(self): pass
    monkeypatch.setattr(collector.requests, 'get', lambda *args, **kwargs: Empty())
    result = collector.collect_one('https://docs.example.org/index')
    assert 'error' in result and 'urls' not in result
