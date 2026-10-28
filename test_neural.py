"""CNN mechanics/contract tests use explicitly synthetic weights, never metrics."""
import json
import tempfile
from pathlib import Path
import pytest
import torch
from phishx.charcnn import CharacterCNN, CNNPredictor, encode, vocabulary, code_hash, text_window
from phishx.model import extractor_hashes,resource_hashes


def test_encoding_is_shared_canonical_and_unknown_is_not_padding():
    chars=vocabulary(['https://example.com/'])
    tokens=encode(['https://EXAMPLE.com/','https://example.com/'],chars)
    assert torch.equal(tokens[0],tokens[1])
    unknown=encode(['https://example.com/☃'],chars)
    assert (unknown==1).any() and (unknown==0).any()
    assert text_window('a'*600+'xyz').endswith('xyz')
    assert len(text_window('a'*600+'xyz'))==512


def test_serialization_roundtrip_and_checksum_failure():
    torch.manual_seed(42)
    chars=vocabulary(['https://example.com/'])
    model=CharacterCNN(len(chars)+2);model.eval()
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);torch.save(model.state_dict(),root/'charcnn.pt')
        import hashlib
        metadata=dict(architecture='charcnn-v1',version='synthetic-test-only',characters=chars,code_sha256=code_hash(),
                      weights_sha256=hashlib.sha256((root/'charcnn.pt').read_bytes()).hexdigest(),extractor_hashes=extractor_hashes(),resource_hashes=resource_hashes())
        (root/'cnn-metadata.json').write_text(json.dumps(metadata))
        loaded=CNNPredictor(root)
        first=loaded.probabilities(['https://example.com/'])
        assert first==loaded.probabilities(['https://example.com/'])
        assert 0<=first[0]<=1
        with (root/'charcnn.pt').open('ab') as file:file.write(b'changed')
        with pytest.raises(ValueError,match='checksum'):CNNPredictor(root)


def test_research_factory_is_explicit(monkeypatch):
    from ml.neural_integration import create_provider
    monkeypatch.delenv('PHISHX_ALLOW_RESEARCH_CASCADE',raising=False)
    with pytest.raises(ValueError,match='Research cascade'):create_provider()


def test_cascade_never_substitutes_classical_shap_for_neural_output():
    import numpy as np
    from phishx.extended_features import analyze_extended
    from ml.neural_integration import CascadeProvider
    from backend.app.main import create_app
    from fastapi.testclient import TestClient
    class SyntheticCascade:
        def predict(self, urls):
            return np.array([.9]),np.array([.55]),np.array([True]),[analyze_extended(urls[0])]
    provider=object.__new__(CascadeProvider)
    provider.cascade=SyntheticCascade();provider.version='synthetic-cascade-test'
    prediction=provider.predict('https://example.com/')
    with pytest.raises(RuntimeError,match='Neural/blended'):provider.explain(prediction)
    with TestClient(create_app(provider=provider,mode='model')) as client:
        assert client.get('/health').json()['cascade_status']=='available'
        response=client.post('/scan',json={'url':'https://example.com/'}).json()
        assert response['model_used']=='cascade' and response['cascade_status']=='available'
        assert response['phishing_probability']==.9
        assert response['explanation_status']=='unavailable' and response['explanation_items']==[]


def test_cascade_only_runs_cnn_inside_gate():
    import numpy as np
    from phishx.cascade import CascadePredictor
    class Forest:
        def predict_proba(self, rows):
            return np.array([[.95,.05],[.5,.5],[.05,.95]])
    class Neural:
        def probabilities(self, urls):
            assert urls==['https://middle.example/']
            return [.9]
    cascade=object.__new__(CascadePredictor)
    cascade.policy={'lower':.3,'upper':.7,'cnn_weight':.5}
    cascade.bundle={'model':Forest(),'feature_names':['feature']}
    cascade.analyze=lambda url:{'features':{'feature':1}}
    cascade.cnn=Neural()
    final,rf,routed,_=cascade.predict(['https://low.example/','https://middle.example/','https://high.example/'])
    assert routed.tolist()==[False,True,False]
    assert final.tolist()==pytest.approx([.05,.7,.95])
    assert rf.tolist()==[.05,.5,.95]


def test_failed_release_cannot_be_started(monkeypatch,tmp_path):
    from ml.completion_integration import create_provider
    (tmp_path/'release-evaluation.json').write_text('{"all_quality_gates_passed":false}')
    monkeypatch.setenv('PHISHX_RELEASE_PATH',str(tmp_path))
    with pytest.raises(ValueError,match='quality gates'):create_provider()
