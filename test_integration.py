"""Synthetic artifact checks for the existing backend contract."""
import hashlib
import tempfile
import unittest
from importlib.resources import files
from pathlib import Path
import joblib
from sklearn.ensemble import RandomForestClassifier
from phishx import FEATURE_NAMES, analyze_url
from phishx.model import extractor_hashes

class IntegrationTests(unittest.TestCase):
    def test_provider_cached_model_and_error_mapping(self):
        from ml.integration import ModelProvider
        from backend.app.providers import InvalidURL
        rows=[list(analyze_url(u)['features'].values()) for u in
              ['https://example.org','https://paypal.com','https://pаypal.com','http://paypal.attacker.org']]
        model=RandomForestClassifier(n_estimators=5,random_state=42).fit(rows,[0,0,1,1])
        bundle=dict(model=model,extractor_hashes=extractor_hashes(),feature_names=list(FEATURE_NAMES),version='synthetic-test-only',
                    resource_hashes={name:hashlib.sha256(files('phishx').joinpath('resources',name).read_bytes()).hexdigest() for name in ('brands.json','confusables.txt')})
        with tempfile.TemporaryDirectory() as tmp:
            artifact=Path(tmp)/'test.joblib';joblib.dump(bundle,artifact)
            provider=ModelProvider(artifact)
            prediction=provider.predict('https://pаypal.com')
            self.assertEqual(list(prediction.context['features']),list(FEATURE_NAMES))
            self.assertEqual(prediction.matched_brand,'paypal')
            self.assertFalse(provider.calibrated)
            self.assertEqual(prediction.phishing_probability,float(model.predict_proba([list(prediction.context['features'].values())])[0,1]))
            with self.assertRaises(InvalidURL):provider.predict('ftp://example.org')
            if provider.adapter is None:
                with self.assertRaises(RuntimeError):provider.explain(prediction)
            else:
                self.assertEqual(provider.explain(prediction).scale,'probability')

            from fastapi.testclient import TestClient
            from backend.app.main import create_app
            with TestClient(create_app(provider=provider, mode='model')) as client:
                self.assertTrue(client.get('/health').json()['ready'])
                response = client.post('/scan', json={'url':'https://pаypal.com'})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()['mode'], 'model')
                self.assertEqual(response.json()['matched_brand'], 'paypal')
                self.assertEqual(client.post('/scan',json={'url':'https://x..com'}).status_code,422)

            stale=dict(bundle)
            stale.pop('extractor_hashes')
            joblib.dump(stale,artifact)
            with self.assertRaisesRegex(ValueError,'Feature extractor changed'):
                ModelProvider(artifact)
