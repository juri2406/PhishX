import pytest
from fastapi.testclient import TestClient
from backend.app.main import create_app
from backend.app.providers import Prediction, AttributionResult, InvalidURL
from backend.app.schemas import Explanation, score_probability


@pytest.mark.parametrize("p,score,band", [(0,0,"Low"),(.30,30,"Low"),(.31,31,"Medium"),(.60,60,"Medium"),(.61,61,"High"),(.80,80,"High"),(.81,81,"Critical"),(1,100,"Critical")])
def test_score_bands(p, score, band):
    assert score_probability(p) == (score, band)


@pytest.mark.parametrize("p", [-.01,1.01,float("nan"),float("inf")])
def test_invalid_probabilities(p):
    with pytest.raises(ValueError): score_probability(p)


@pytest.mark.parametrize("body", [{}, {"url":123}, {"url":""}, {"url":"javascript:alert(1)"}, {"url":"https://ex ample.com"}, {"url":"https://example.com\n"}, {"url":"https://example.com/"+"a"*2048}, {"url":"https://example.com/","extra":True}])
def test_request_validation(body):
    with TestClient(create_app(mode="fixture")) as client:
        response = client.post("/scan", json=body)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_fixture_is_explicit_and_only_supports_known_samples():
    with TestClient(create_app(mode="fixture")) as client:
        assert client.get("/health").json()["ready"]
        r = client.post("/scan",json={"url":"https://example.com/"}).json()
        assert r["mode"] == "fixture" and r["model_version"] == "fixture-v1-untrained"
        assert r["explanation_items"] == [] and r["explanation_status"] == "fixture"
        assert r["cascade_status"] == "not_implemented"
        assert client.post("/scan",json={"url":"https://unknown.example/"}).status_code == 422


def test_missing_model_is_not_a_fake_prediction(monkeypatch):
    monkeypatch.delenv("PHISHX_PROVIDER", raising=False)
    with TestClient(create_app(mode="model")) as client:
        assert client.get("/health").json()["ready"] is False
        assert client.post("/scan",json={"url":"https://example.com/"}).status_code == 503


class FakeProvider:
    version, calibrated = "unit-test-only", False
    def predict(self,url):
        if url == "https://bad": raise InvalidURL("Malformed host")
        return Prediction("example.com",.73,[])
    def explain(self,prediction):
        return AttributionResult([Explanation(feature="test",observed_value=4,contribution=.2,reason="Test attribution")],"probability")


def test_injected_provider_and_explanations():
    with TestClient(create_app(FakeProvider(),"model")) as client:
        r = client.post("/scan",json={"url":"https://example.com/"}).json()
        assert r["risk_score"] == 73 and r["risk_level"] == "High"
        assert r["explanation_status"] == "available"
        assert r["explanation_items"][0]["feature"] == "test"
        assert client.post("/scan",json={"url":"https://bad"}).status_code == 422


def test_parser_error_has_recovery_message_and_original_detail():
    with TestClient(create_app(FakeProvider(), "model")) as client:
        response = client.post("/scan", json={"url": "https://bad"})
        error = response.json()["error"]
        assert response.status_code == 422 and error["code"] == "INVALID_URL"
        assert "retry" in error["message"]
        assert error["details"] == [{"field": "url", "message": "Malformed host"}]


def test_explanation_failure_preserves_prediction():
    class Broken(FakeProvider):
        def explain(self,prediction): raise RuntimeError("bad SHAP")
    with TestClient(create_app(Broken(),"model")) as client:
        r = client.post("/scan",json={"url":"https://example.com/"}).json()
        assert r["risk_score"] == 73 and r["explanation_status"] == "unavailable"
        assert r["explanation_items"] == []


def test_invalid_provider_output_returns_structured_error():
    class Broken(FakeProvider):
        def predict(self,url): return Prediction("example.com",float("nan"),[])
    with TestClient(create_app(Broken(),"model")) as client:
        r=client.post("/scan",json={"url":"https://example.com/"})
        assert r.status_code == 500 and r.json()["error"]["code"] == "INFERENCE_FAILED"


def test_factory_is_called_once_at_startup(monkeypatch):
    import types
    calls=[]
    def factory():
        calls.append("loaded")
        return FakeProvider()
    monkeypatch.setenv("PHISHX_PROVIDER","test.integration:create_provider")
    monkeypatch.setattr("backend.app.main.importlib.import_module",lambda name:types.SimpleNamespace(create_provider=factory))
    with TestClient(create_app(mode="model")) as client:
        for _ in range(3):
            assert client.post("/scan",json={"url":"https://example.com/"}).status_code == 200
        assert calls == ["loaded"]


def test_factory_failure_leaves_api_not_ready(monkeypatch):
    monkeypatch.setenv("PHISHX_PROVIDER","does_not_exist:create_provider")
    with TestClient(create_app(mode="model")) as client:
        assert client.get("/health").json()["ready"] is False
        assert client.post("/scan",json={"url":"https://example.com/"}).json()["error"]["code"] == "MODEL_NOT_READY"


def test_top_three_contributions_are_sorted():
    class Several(FakeProvider):
        def explain(self,prediction):
            return AttributionResult([Explanation(feature=str(i),observed_value=i,contribution=i/10,reason="Test") for i in [2,4,1,3]],"probability")
    with TestClient(create_app(Several(),"model")) as client:
        result=client.post("/scan",json={"url":"https://example.com/"}).json()
        assert [item["feature"] for item in result["explanation_items"]] == ["4","3","2"]
