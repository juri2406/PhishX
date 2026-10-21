"""Exact four-component Shapley attribution of the full frozen URL pipeline.

All 16 coalitions are evaluated as URL text. No network requests, proxy model,
TreeSHAP relabelling or neural-gradient approximation is involved.
"""
from math import factorial,isfinite
from urllib.parse import urlsplit,urlunsplit
from .urls import normalize_url

REFERENCE='http://a.b'
COMPONENTS=('url_scheme','url_authority','url_path','url_query')


def explain_components(cascade, url, expected_probability):
    original=urlsplit(normalize_url(url).raw)
    baseline=urlsplit(REFERENCE)
    observed=[original.scheme,original.netloc,original.path,original.query]
    reference=[baseline.scheme,baseline.netloc,baseline.path,baseline.query]
    coalitions=[]
    for mask in range(16):
        pieces=[observed[i] if mask&(1<<i) else reference[i] for i in range(4)]
        coalitions.append(urlunsplit((*pieces,original.fragment)))
    values=cascade.predict(coalitions)[0]
    contributions={}
    for i,name in enumerate(COMPONENTS):
        contributions[name]=sum(factorial(mask.bit_count())*factorial(3-mask.bit_count())/factorial(4)*(float(values[mask|(1<<i)])-float(values[mask])) for mask in range(16) if not mask&(1<<i))
    residual=float(expected_probability)-float(values[0])-sum(contributions.values())
    if not all(isfinite(v) for v in contributions.values()) or abs(residual)>1e-5:
        raise ValueError('URL-component Shapley additivity failed')
    return {'method':'exact_url_component_shapley','reference_url':coalitions[0],'baseline_probability':float(values[0]),
            'target_probability':float(expected_probability),'contributions':contributions,'additivity_residual':residual,
            'observed':dict(zip(COMPONENTS,observed)),
            'held_constant':'URL fragment, when present',
            'scope':'Full frozen cascade, relative to the stated URL-component reference. This explains model behavior, not real-world site safety.'}
