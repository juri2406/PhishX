"""Release-candidate consensus pipeline with exact component Shapley explanations."""
import hashlib,json,os
from pathlib import Path
from ml.neural_integration import CascadeProvider
from phishx.component_shapley import explain_components
from backend.app.providers import AttributionResult
from backend.app.schemas import Explanation


class ReleaseProvider(CascadeProvider):
    model_profile='release_cascade'
    notice='Local evaluation release: RF and character-CNN cascade. Scores are uncalibrated and can be wrong; see the evaluation report.'

    def __init__(self,directory,classical):
        super().__init__(directory,classical)
        policy=self.cascade.policy
        if policy.get('fusion') not in ('minimum','blend'):
            raise ValueError('Unknown release fusion policy')
        code=Path(__file__).with_name('phishx')/'component_shapley.py'
        if hashlib.sha256(code.read_bytes()).hexdigest()!=policy['explanation_code_sha256']:
            raise ValueError('Explanation code checksum mismatch')

    def predict(self,url):
        prediction=super().predict(url)
        prediction.context['submitted_url']=url
        return prediction

    def explain(self,prediction):
        audit=explain_components(self.cascade,prediction.context['submitted_url'],prediction.phishing_probability)
        items=[Explanation(feature=name,observed_value=audit['observed'][name],contribution=value,
                           reason='The '+name.removeprefix('url_')+' increased this model output relative to the reference URL.')
               for name,value in audit['contributions'].items() if value>0]
        items.sort(key=lambda x:x.contribution,reverse=True)
        return AttributionResult(items[:3],'probability',method='exact_url_component_shapley',audit=audit)


def create_provider():
    directory=Path(os.environ.get('PHISHX_RELEASE_PATH','artifacts/release-v3'))
    release=json.loads((directory/'release-evaluation.json').read_text())
    if not release.get('all_quality_gates_passed'):
        raise ValueError('Release candidate did not pass its registered quality gates')
    provider=ReleaseProvider(directory,Path(os.environ['PHISHX_MODEL_PATH']))
    if release.get('policy') != provider.cascade.policy:
        raise ValueError('Release evaluation does not match the frozen policy')
    return provider
