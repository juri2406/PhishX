"""Synthetic mechanics tests only; no claimed phishing-model evaluation."""
import pytest
np = pytest.importorskip("numpy")
pytest.importorskip("shap")
from sklearn.ensemble import RandomForestClassifier
from backend.app.shap_adapter import TreeShapAdapter


@pytest.fixture
def adapter():
    row = np.array([[0,0],[0,1],[1,0],[1,1]] * 8)
    labels = np.array([0,0,1,1] * 8)
    model=RandomForestClassifier(n_estimators=12,random_state=4).fit(row,labels)
    return TreeShapAdapter(model,["synthetic_a","synthetic_b"],1,"probability",lambda x:model.predict_proba(x)[0,1],{})


def test_real_tree_shap_additivity_and_positive_items(adapter):
    result=adapter.explain({"synthetic_a":1,"synthetic_b":0})
    assert result.scale == "probability"
    assert result.items and all(x.contribution > 0 for x in result.items)


def test_feature_order_must_match(adapter):
    with pytest.raises(ValueError,match="ordered"):
        adapter.explain({"synthetic_b":0,"synthetic_a":1})


def test_nonfinite_features_rejected(adapter):
    with pytest.raises(ValueError,match="Nonfinite"):
        adapter.explain({"synthetic_a":np.nan,"synthetic_b":0})


def test_incorrect_output_scale_rejected(adapter):
    adapter.output_fn=lambda x:100
    with pytest.raises(ValueError,match="additivity"):
        adapter.explain({"synthetic_a":1,"synthetic_b":0})
