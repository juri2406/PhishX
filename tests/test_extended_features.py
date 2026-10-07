"""Versioned feature compatibility and encoding semantics checks."""
from pathlib import Path
import joblib
import pytest
from sklearn.ensemble import RandomForestClassifier
from phishx.extended_features import analyze_extended, EXTENDED_FEATURE_NAMES, extended_hashes
from phishx.model import extractor_hashes, resource_hashes
from phishx.robustness import variant
from urllib.parse import urlsplit, unquote


def test_percent_encoding_skips_existing_escape():
    original='https://example.org/%61bc'
    changed=variant(original,'percent_encoding')
    assert changed=='https://example.org/%61%62c'
    assert unquote(urlsplit(changed).path)==unquote(urlsplit(original).path)
    assert variant('https://example.org/%61%62','percent_encoding') is None


def test_extended_profile_and_shap_reject_stale_hash(tmp_path):
    from ml.integration import ModelProvider
    urls=['https://paypal.com/login','https://example.org/a/123','https://pаypal.com/login','http://paypal.attacker.org']
    features=[analyze_extended(u)['features'] for u in urls]
    assert list(features[0])==list(EXTENDED_FEATURE_NAMES)
    assert features[0]['known_brand_domain']==1
    assert features[2]['known_brand_domain']==0
    assert features[1]['host_digit_count']==0
    assert features[1]['path_digit_fraction']>0
    model=RandomForestClassifier(n_estimators=5,random_state=42).fit([[f[n] for n in EXTENDED_FEATURE_NAMES] for f in features],[0,0,1,1])
    bundle=dict(model=model,version='synthetic-extended-only',feature_profile='extended-v1',feature_names=list(EXTENDED_FEATURE_NAMES),
        extended_extractor_hashes=extended_hashes(),extractor_hashes=extractor_hashes(),resource_hashes=resource_hashes())
    artifact=tmp_path/'synthetic.joblib';joblib.dump(bundle,artifact)
    provider=ModelProvider(artifact)
    prediction=provider.predict(urls[2])
    explanation=provider.explain(prediction)
    assert explanation.scale=='probability'
    assert prediction.phishing_probability==float(model.predict_proba([[features[2][n] for n in EXTENDED_FEATURE_NAMES]])[0,1])
    bundle['extended_extractor_hashes']={};joblib.dump(bundle,artifact)
    with pytest.raises(ValueError,match='Extended feature extractor'):
        ModelProvider(artifact)
