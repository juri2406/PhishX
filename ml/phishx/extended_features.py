"""Versioned additional numeric signals; none overrides a model verdict."""
from collections import Counter
import hashlib
import math
from pathlib import Path
from .features import analyze_url, FEATURE_NAMES

EXTENDED_FEATURE_NAMES = FEATURE_NAMES + ('host_digit_count','path_digit_fraction',
    'path_segment_count','path_entropy','government_suffix','known_brand_domain')


def extended_hashes():
    return {'extended_features.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def analyze_extended(value):
    result=analyze_url(value); normalized=result['normalized']
    host=normalized['ascii_host']; path=normalized['path'] or '/'
    counts=Counter(path)
    entropy=-sum((n/len(path))*math.log2(n/len(path)) for n in counts.values())
    result['features'].update(dict(host_digit_count=sum(c.isdigit() for c in host),
        path_digit_fraction=sum(c.isdigit() for c in path)/len(path),
        path_segment_count=len([segment for segment in path.split('/') if segment]),
        path_entropy=entropy,
        government_suffix=int(normalized['suffix'] in ('gov','gov.uk','gov.in','gov.au','gov.br','gouv.fr')),
        known_brand_domain=int(result['brand_match']['legitimate_brand_domain'])))
    return result
