from collections import Counter
import math
import re
from .urls import normalize_url
from .skeleton import match_brand, skeleton, mapping

FEATURE_NAMES = ('url_length', 'host_length', 'digit_count', 'hyphen_count',
                 'subdomain_count', 'host_entropy', 'is_ip', 'https_explicit',
                 'punycode_present', 'percent_encoding_present', 'userinfo_present',
                 'non_ascii_host', 'confusable_non_ascii', 'brand_distance',
                 'brand_impersonation', 'brand_in_subdomain', 'path_length', 'query_length')

def analyze_url(value):
    u = normalize_url(value); match = match_brand(u)
    counts = Counter(u.ascii_host)
    entropy = -sum((n/len(u.ascii_host))*math.log2(n/len(u.ascii_host)) for n in counts.values())
    non_ascii_confusable = any(ord(c)>127 and mapping().get(c, c) != c for c in u.unicode_host)
    subdomain_brand = bool(u.subdomain and not match['legitimate_brand_domain'] and
                          any(skeleton(label) == skeleton(name)
                              for label in u.subdomain.split('.') for name in mapping_brands()))
    values = (len(u.raw), len(u.ascii_host), sum(c.isdigit() for c in u.raw),
              u.ascii_host.count('-'), len(u.subdomain.split('.')) if u.subdomain else 0,
              entropy, int(u.is_ip), int(u.explicit_scheme and u.scheme == 'https'),
              int('xn--' in u.ascii_host), int(bool(re.search(r'%[0-9a-fA-F]{2}', u.raw))),
              int(u.has_userinfo), int(any(ord(c)>127 for c in u.unicode_host)),
              int(non_ascii_confusable), match['distance'], int(match['impersonation_signal']),
              int(subdomain_brand), len(u.path), len(u.query))
    return {'normalized': u.to_dict(), 'brand_match': match,
            'features': dict(zip(FEATURE_NAMES, values))}

def mapping_brands():
    from .skeleton import brands
    return brands().keys()
