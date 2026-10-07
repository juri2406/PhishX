"""Collect navigation candidates from a fixed reviewed official-source list.

Only seed pages are fetched. Linked URLs remain text; this is not a crawler.
Owning-domain navigation is a label basis, not a guarantee against compromise.
"""
import argparse
import csv
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
import requests
from phishx.urls import normalize_url, InvalidURL


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.title = []; self.in_title = False
    def handle_starttag(self, tag, attrs):
        if tag == 'title': self.in_title = True
        if tag == 'a':
            href = dict(attrs).get('href')
            if href: self.links.append(href)
    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
    def handle_data(self, data):
        if self.in_title: self.title.append(data)


def collect_one(seed):
    try:
        response = requests.get(seed, timeout=25,
            headers={'User-Agent': 'PhishX academic URL-text research; one seed-page request'})
        response.raise_for_status()
        original = normalize_url(seed)
        if normalize_url(response.url).registrable_domain != original.registrable_domain:
            raise ValueError('Seed redirected outside reviewed owning domain')
        if 'text/html' not in response.headers.get('Content-Type', ''):
            raise ValueError('Not an HTML navigation source')
        parser = Links(); parser.feed(response.text)
        if response.status_code != 200 or not ''.join(parser.title).strip():
            raise ValueError('Seed needs HTTP 200 and an inspectable page title')
        urls = set()
        for href in [response.url] + parser.links:
            parts = urlsplit(urljoin(response.url, href))
            if parts.scheme not in ('http', 'https') or parts.query: continue
            url = urlunsplit(parts._replace(fragment=''))
            try:
                parsed = normalize_url(url)
                # Restrict to seed hostname: no user-hosted tenants or external links.
                if parsed.ascii_host != normalize_url(response.url).ascii_host: continue
                if parsed.has_userinfo or not parsed.path: continue
                if parsed.path.lower().endswith(('.zip', '.png', '.jpg', '.svg', '.pdf', '.gz')): continue
                urls.add(parsed.canonical)
            except InvalidURL: continue
        urls = sorted(urls)
        # Deterministic sampling covers paths throughout the navigation list.
        urls = sorted(urls, key=lambda url: hashlib.sha256(url.encode()).hexdigest())[:100]
        return {'seed': seed, 'final_seed': response.url, 'title': ''.join(parser.title).strip(),
                'domain': original.registrable_domain, 'status': response.status_code,
                'seed_html_sha256': hashlib.sha256(response.content).hexdigest(), 'urls': urls}
    except Exception as exc:
        return {'seed': seed, 'error': str(exc)}


def collect(seeds, output):
    output = Path(output)
    if output.exists(): raise ValueError('Choose a new output')
    inputs = json.loads(Path(seeds).read_text())
    with ThreadPoolExecutor(max_workers=4) as pool:
        sources = list(pool.map(collect_one, inputs))
    now = datetime.now(timezone.utc).isoformat()
    rows = [dict(url=url, label=0, source='official-navigation:' + source['seed'],
                 collected_at=now, family='original', group_domain='')
            for source in sources for url in source.get('urls', [])]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['url','label','source','collected_at','family','group_domain'])
        writer.writeheader(); writer.writerows(rows)
    manifest = {'collected_at': now, 'sources': sources,
                'label_basis': 'Fixed reviewed official organization/documentation seeds; same-host public navigation links. Individual linked pages are not fetched or independently certified.',
                'limitation': 'Convenience sample, not general web prevalence or a guarantee against compromised official pages.',
                'input_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}
    output.with_suffix('.sources.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({'rows': len(rows), 'sources': [{k:v for k,v in s.items() if k!='urls'} for s in sources]}, indent=2))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('seeds'); p.add_argument('output')
    a=p.parse_args(); collect(a.seeds,a.output)
