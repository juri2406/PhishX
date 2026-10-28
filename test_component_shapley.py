import numpy as np
import pytest
from phishx.component_shapley import explain_components


def test_exact_components_include_full_pipeline_and_add_up():
    class Pipeline:
        def predict(self, urls):
            # Synthetic coalition game, explicitly not detector predictions.
            return np.array([.1+.2*('target.test' in u)+.3*('/login' in u) for u in urls]),None,None,None
    result=explain_components(Pipeline(),'https://target.test/login',.6)
    assert result['baseline_probability']==pytest.approx(.1)
    assert result['contributions']['url_authority']==pytest.approx(.2)
    assert result['contributions']['url_path']==pytest.approx(.3)
    assert abs(result['additivity_residual'])<1e-10


def test_mismatched_target_probability_is_rejected():
    class Pipeline:
        def predict(self, urls):return np.zeros(len(urls)),None,None,None
    with pytest.raises(ValueError,match='additivity'):
        explain_components(Pipeline(),'https://target.test/',.5)


def test_coalitions_preserve_valid_maximum_length_inputs():
    from phishx.urls import normalize_url
    class Pipeline:
        def predict(self, urls):
            assert all(len(u)<=2048 for u in urls)
            for u in urls:normalize_url(u)
            return np.zeros(len(urls)),None,None,None
    url='https://a.b/'+('a'*(2048-len('https://a.b/')))
    assert explain_components(Pipeline(),url,0.)['additivity_residual']==0


def test_fragment_is_held_constant_for_raw_observation_features():
    class Pipeline:
        def predict(self, urls):return np.array([.4 if '%61' in u else .1 for u in urls]),None,None,None
    audit=explain_components(Pipeline(),'https://target.test/#%61',.4)
    assert audit['reference_url'].endswith('#%61')
    assert sum(audit['contributions'].values())==pytest.approx(0)
