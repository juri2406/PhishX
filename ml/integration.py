"""Startup-loaded bridge to Person 2's existing provider contract."""
import hashlib
import os
from importlib.resources import files
import joblib
from phishx import FEATURE_NAMES, analyze_url, InvalidURL as ParseError
from backend.app.providers import Prediction, InvalidURL
from backend.app.schemas import Signal

class ModelProvider:
    calibrated = False

    def __init__(self, path):
        bundle = joblib.load(path)
        if bundle['feature_names'] != list(FEATURE_NAMES):
            raise ValueError('Feature schema mismatch')
        for name, expected in bundle['resource_hashes'].items():
            if hashlib.sha256(files('phishx').joinpath('resources', name).read_bytes()).hexdigest() != expected:
                raise ValueError('Resource checksum mismatch')
        self.model = bundle['model']
        if list(self.model.classes_) != [0, 1]:
            raise ValueError('Expected binary labels 0=benign, 1=phishing')
        self.version = bundle['version']
        self.index = list(self.model.classes_).index(1)
        self.adapter = None
        self.explanation_error = None
        try:
            from backend.app.shap_adapter import TreeShapAdapter
            self.adapter = TreeShapAdapter(self.model, list(FEATURE_NAMES), 1, 'probability',
                lambda row: self.model.predict_proba(row)[0, self.index], {})
        except Exception as exc:
            self.explanation_error = type(exc).__name__

    def predict(self, url):
        try:
            analysis = analyze_url(url)
        except ParseError as exc:
            raise InvalidURL(str(exc)) from exc
        features = analysis['features']
        row = [[features[name] for name in FEATURE_NAMES]]
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
