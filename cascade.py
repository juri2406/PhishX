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
        if self.policy.get('fusion', 'blend') not in {'blend', 'minimum', 'meta', 'ranked'}:
            raise ValueError('Unknown cascade fusion')
        self.meta = None
        if self.policy.get('fusion') in ('meta','ranked'):
            import joblib
            path=self.directory/'fusion.joblib'
            if hashlib.sha256(path.read_bytes()).hexdigest()!=self.policy['fusion_sha256']:
                raise ValueError('Fusion model checksum mismatch')
            self.meta=joblib.load(path)  # Trusted local frozen handoff only.
        self.ranks = None
        if self.policy.get('fusion') == 'ranked':
            import joblib
            from .ranked_context import CONTEXT_NAMES
            context_code=Path(__file__).with_name('ranked_context.py')
            if hashlib.sha256(context_code.read_bytes()).hexdigest()!=self.policy['context_code_sha256'] or list(CONTEXT_NAMES)!=self.policy['context_names']:
                raise ValueError('Context feature code/schema mismatch')
            path=self.directory/'rank-context.joblib'
            if hashlib.sha256(path.read_bytes()).hexdigest()!=self.policy['rank_context_sha256']:
                raise ValueError('Ranking snapshot checksum mismatch')
            self.ranks=joblib.load(path)
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
            if self.policy.get('fusion') == 'ranked':
                from .ranked_context import context_matrix
                selected=[a for a,r in zip(analyses,routed) if r]
                final[routed]=self.meta.predict_proba(context_matrix(classical[routed],cnn,selected,self.ranks))[:,1]
                return final, classical, routed, analyses
            if self.policy.get('fusion') == 'meta':
                final[routed] = self.meta.predict_proba(fusion_features(classical[routed],cnn))[:,1]
                return final, classical, routed, analyses
            final[routed] = (np.minimum(classical[routed], cnn) if self.policy.get('fusion') == 'minimum'
                             else (1-weight)*classical[routed] + weight*cnn)
        return final, classical, routed, analyses


def fusion_features(classical, neural):
    """One shared train/inference transform; bounded logits limit numeric drift."""
    return np.column_stack([np.log(p/(1-p)) for p in (np.clip(classical,.001,.999),np.clip(neural,.001,.999))])
