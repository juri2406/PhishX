"""Model-owner inference adapter; does not change the existing API or SHAP path."""
import hashlib
import json
from pathlib import Path

import numpy as np

from .features import analyze_url
from .model import load_bundle


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def routing_mask(probabilities, low, high):
    if not 0 <= low <= .5 <= high <= 1:
        raise ValueError('Routing interval must surround 0.5 within [0,1].')
    probabilities = np.asarray(probabilities, dtype=float)
    if not np.all(np.isfinite(probabilities)) or np.any((probabilities < 0) | (probabilities > 1)):
        raise ValueError('Invalid phishing probabilities.')
    # A zero-width gate explicitly disables escalation.
    return (probabilities >= low) & (probabilities <= high) & (low < high)


class ClassicalPredictor:
    def __init__(self, artifact):
        self.bundle = load_bundle(artifact)
        self.analyze = analyze_url
        if self.bundle.get('feature_profile') == 'extended-v1':
            from .extended_features import analyze_extended
            self.analyze = analyze_extended

    def probabilities(self, urls):
        if not urls:
            return np.empty(0)
        names = self.bundle['feature_names']
        matrix = [[analysis['features'][name] for name in names]
                  for analysis in map(self.analyze, urls)]
        return self.bundle['model'].predict_proba(matrix)[:, 1]


class CascadePredictor:
    def __init__(self, classical, cnn, low, high):
        routing_mask([], low, high)
        self.classical, self.cnn = classical, cnn
        self.low, self.high = low, high

    @classmethod
    def load(cls, config_path, classical_path, cnn_path):
        from .charcnn import CNNPredictor
        config = json.loads(Path(config_path).read_text(encoding='utf-8'))
        if config.get('format') != 'phishx-cascade-v1':
            raise ValueError('Unsupported cascade configuration.')
        if config['classical_sha256'] != file_hash(classical_path) or config['cnn_sha256'] != file_hash(cnn_path):
            raise ValueError('Cascade artifacts differ from validation-selected artifacts.')
        classical, cnn = ClassicalPredictor(classical_path), CNNPredictor.load(cnn_path)
        hashes = config['split_sha256']
        for predictor_hashes in (classical.bundle.get('split_sha256', {}), cnn.metadata['split_sha256']):
            if any(predictor_hashes.get(name) != hashes.get(name) for name in ('train', 'validation', 'test')):
                raise ValueError('Cascade dataset lineage mismatch.')
        return cls(classical, cnn, config['low'], config['high'])

    def probabilities_with_paths(self, urls):
        probability = np.asarray(self.classical.probabilities(urls), dtype=float).copy()
        mask = routing_mask(probability, self.low, self.high)
        if mask.any():
            probability[mask] = self.cnn.probabilities([url for url, selected in zip(urls, mask) if selected])
        paths = np.where(mask, 'char_cnn', 'classical').tolist()
        return probability, paths

    def probabilities(self, urls):
        return self.probabilities_with_paths(urls)[0]

    def predict(self, url):
        probabilities, paths = self.probabilities_with_paths([url])
        probability = float(probabilities[0])
        score = round(100 * probability)
        return dict(phishing_probability=probability, risk_score=score,
                    risk_level='Low' if score <= 30 else 'Medium' if score <= 60 else 'High' if score <= 80 else 'Critical',
                    model_used=paths[0], cascade_status='implemented', probability_calibrated=False,
                    explanation_status='cnn_attribution_unavailable' if paths[0] == 'char_cnn' else 'use_existing_classical_explainer')
