"""Explicit research-cascade bridge. The classical provider remains the default."""
import os
from pathlib import Path
from phishx.cascade import CascadePredictor
from phishx.urls import InvalidURL as ParseError
from backend.app.providers import Prediction, InvalidURL
from backend.app.schemas import Signal
from ml.integration import ModelProvider


class CascadeProvider:
    calibrated = False
    cascade_status = 'available'

    def __init__(self, directory, classical):
        import torch
        torch.set_num_threads(4)
        self.cascade = CascadePredictor(directory,classical)
        self.classical = ModelProvider(classical)
        self.version = self.cascade.version

    def predict(self, url):
        try:
            final,rf,routed,analyses = self.cascade.predict([url])
        except ParseError as exc:
            raise InvalidURL(str(exc)) from exc
        analysis=analyses[0];match=analysis['brand_match']
        signals=[Signal(name=name,value=float(value),description='Observed '+name.replace('_',' ')) for name,value in analysis['features'].items()]
        return Prediction(analysis['normalized']['ascii_host'],float(final[0]),signals,match['closest_brand'],match['distance'],
                          {'features':analysis['features'],'model_used':'cascade' if routed[0] else 'classical','cascade_status':'available',
                           'cnn_routed':bool(routed[0]),'classical_probability':float(rf[0])})

    def explain(self, prediction):
        if prediction.context['cnn_routed']:
            raise RuntimeError('Neural/blended output has no validated SHAP adapter; classical SHAP would not explain this score.')
        return self.classical.explain(prediction)


def create_provider():
    if os.getenv('PHISHX_ALLOW_RESEARCH_CASCADE') != '1':
        raise ValueError('Research cascade requires PHISHX_ALLOW_RESEARCH_CASCADE=1; it is not promoted by default.')
    return CascadeProvider(Path(os.environ['PHISHX_NEURAL_PATH']),Path(os.environ['PHISHX_MODEL_PATH']))
