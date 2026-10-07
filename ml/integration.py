"""Startup-loaded bridge to Person 2's existing provider contract."""
import os
from phishx import FEATURE_NAMES, analyze_url, InvalidURL as ParseError
from backend.app.providers import Prediction, InvalidURL
from phishx.model import load_bundle
from backend.app.schemas import Signal

class ModelProvider:
    calibrated = False

    def __init__(self, path):
        bundle = load_bundle(path)
        self.feature_names = bundle['feature_names']
        self.analyze = analyze_url
        if bundle.get('feature_profile') == 'extended-v1':
            from phishx.extended_features import analyze_extended
            self.analyze = analyze_extended
        self.calibrated = bundle.get('probability_calibrated', False)
        self.model = bundle['model']
        if list(self.model.classes_) != [0, 1]:
            raise ValueError('Expected binary labels 0=benign, 1=phishing')
        self.version = bundle['version']
        self.index = list(self.model.classes_).index(1)
        self.adapter = None
        self.explanation_error = None
        try:
            from backend.app.shap_adapter import TreeShapAdapter
            self.adapter = TreeShapAdapter(self.model, self.feature_names, 1, 'probability',
                lambda row: self.model.predict_proba(row)[0, self.index], {})
        except Exception as exc:
            self.explanation_error = type(exc).__name__

    def predict(self, url):
        try:
            analysis = self.analyze(url)
        except ParseError as exc:
            raise InvalidURL(str(exc)) from exc
        features = analysis['features']
        row = [[features[name] for name in self.feature_names]]
        probability = float(self.model.predict_proba(row)[0, self.index])
        match = analysis['brand_match']
        signals = [Signal(name=name, value=float(value), description='Observed '+name.replace('_',' ')) for name,value in features.items()]
        return Prediction(analysis['normalized']['ascii_host'], probability, signals,
                          match['closest_brand'], match['distance'], {'features': features})

    def explain(self, prediction):
        if self.adapter is None:
            raise RuntimeError('SHAP initialization unavailable: '+str(self.explanation_error))
        return self.adapter.explain(prediction.context['features'])

def create_provider():
    path = os.environ.get('PHISHX_MODEL_PATH')
    if not path:
        raise ValueError('Set PHISHX_MODEL_PATH to a trusted frozen artifact')
    return ModelProvider(path)
