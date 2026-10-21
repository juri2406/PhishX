"""Frozen uncertainty gate. No live-network observations enter either model."""
import hashlib
import json
from pathlib import Path
import numpy as np
from .model import load_bundle
from .charcnn import CNNPredictor


class CascadePredictor:
    def __init__(self, directory, classical_path):
        self.directory = Path(directory)
        self.policy = json.loads((self.directory/'cascade-policy.json').read_text())
        if not (0 <= self.policy['lower'] <= self.policy['upper'] <= 1 and 0 <= self.policy['cnn_weight'] <= 1):
            raise ValueError('Invalid cascade gate or blend weight')
        if hashlib.sha256(Path(classical_path).read_bytes()).hexdigest() != self.policy['classical_sha256']:
            raise ValueError('Cascade classical artifact mismatch')
        if self.policy.get('cascade_code_sha256') and hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != self.policy['cascade_code_sha256']:
            raise ValueError('Cascade code checksum mismatch')
        if self.policy.get('fusion', 'blend') not in {'blend', 'minimum'}:
            raise ValueError('Unknown cascade fusion')
        self.bundle = load_bundle(classical_path)
        self.cnn = CNNPredictor(directory)
        if self.cnn.version != self.policy['cnn_version']:
            raise ValueError('Cascade CNN version mismatch')
        from .features import analyze_url
        from .extended_features import analyze_extended
        self.analyze = analyze_extended if self.bundle.get('feature_profile') == 'extended-v1' else analyze_url
        self.version = self.policy['version']

    def predict(self, urls):
        analyses = [self.analyze(url) for url in urls]
        rows = [[a['features'][name] for name in self.bundle['feature_names']] for a in analyses]
        classical = self.bundle['model'].predict_proba(rows)[:,1]
        routed = (classical >= self.policy['lower']) & (classical <= self.policy['upper'])
        final = classical.copy()
        if routed.any():
            cnn = np.array(self.cnn.probabilities([u for u,r in zip(urls,routed) if r]))
            weight = self.policy['cnn_weight']
            final[routed] = (np.minimum(classical[routed], cnn) if self.policy.get('fusion') == 'minimum'
                             else (1-weight)*classical[routed] + weight*cnn)
        return final, classical, routed, analyses
