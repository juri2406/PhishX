"""Versioned NFD/map/NFD confusable skeleton for domain comparisons.
This is a scoped comparison tool, not full UTS 39 conformance or bidi processing.
"""
from functools import lru_cache
from importlib.resources import files
import json
import unicodedata

@lru_cache(maxsize=1)
def mapping():
    result = {}
    for line in files('phishx').joinpath('resources/confusables.txt').read_text(encoding='utf-8').splitlines():
        payload = line.split('#', 1)[0].strip()
        if payload:
            source, target, *_ = payload.split(';')
            result[''.join(chr(int(x, 16)) for x in source.split())] = ''.join(chr(int(x, 16)) for x in target.split())
    return result

@lru_cache(maxsize=8192)
def skeleton(text):
    decomposed = unicodedata.normalize('NFD', text.lower())
    return unicodedata.normalize('NFD', ''.join(mapping().get(c, c) for c in decomposed))

def edit_distance(a, b):
    row = list(range(len(b)+1))
    for i, x in enumerate(a, 1):
        nxt = [i]
        for j, y in enumerate(b, 1):
            nxt.append(min(nxt[-1]+1, row[j]+1, row[j-1]+(x != y)))
        row = nxt
    return row[-1]

@lru_cache(maxsize=1)
def brands():
    return json.loads(files('phishx').joinpath('resources/brands.json').read_text())

def match_brand(url):
    legitimate = any(url.registrable_domain in domains for domains in brands().values())
    if url.is_ip:
        return dict(closest_brand=None, distance=1.0, candidate=None,
                    legitimate_brand_domain=False, impersonation_signal=False)
    candidates = [url.domain_label] + [p for p in url.domain_label.split('-') if len(p) >= 3]
    if url.subdomain:
        candidates += url.subdomain.split('.')
    best = (1.0, None, None)
    for name, domains in brands().items():
        for target in [name] + [d.split('.')[0] for d in domains]:
            target_sk = skeleton(target)
            for candidate in candidates:
                candidate_sk = skeleton(candidate)
                distance = edit_distance(candidate_sk, target_sk) / max(len(candidate_sk), len(target_sk), 1)
                if distance < best[0]:
                    best = distance, name, candidate
    distance, name, candidate = best
    return dict(closest_brand=name, distance=distance, candidate=candidate,
                legitimate_brand_domain=legitimate,
                impersonation_signal=bool(not legitimate and distance <= .25))
