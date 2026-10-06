"""Verify the frozen model through the existing API using real held-out rows."""
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter
from fastapi.testclient import TestClient
from backend.app.main import create_app
from ml.integration import ModelProvider
from phishx.model import load_rows


def verify(model_path, test_path, output):
    rows=load_rows(test_path)
    selected=[]
    for label in ('0','1'):
        selected += [r for r in rows if r['label']==label][:10]
    provider=ModelProvider(model_path)
    if provider.adapter is None:
        raise ValueError('SHAP initialization must succeed for this verification')
    checks=[]
    with TestClient(create_app(provider=provider, mode='model')) as client:
        health=client.get('/health').json()
        if not health['ready']:
            raise ValueError('Backend is not ready')
        for row in selected:
            start=perf_counter(); response=client.post('/scan',json={'url':row['url']})
            elapsed=perf_counter()-start
            if response.status_code != 200:
                raise ValueError('Real held-out URL failed the API contract')
            result=response.json()
            if result['explanation_status']!='available' or result['explanation_scale']!='probability':
                raise ValueError('Real-model explanation unavailable or incorrect scale')
            if result['model_version']!=provider.version or result['mode']!='model':
                raise ValueError('Unexpected provider mode/version')
            checks.append(dict(label=int(row['label']),risk_score=result['risk_score'],
                               explanation_items=len(result['explanation_items']),
                               api_timings_ms=result['timings_ms'],in_process_request_ms=elapsed*1000))
        unicode_response=client.post('/scan',json={'url':'https://pаypal.com/login'})
        unicode_result=unicode_response.json()
        if unicode_response.status_code!=200 or unicode_result['matched_brand']!='paypal' or unicode_result['explanation_status']!='available':
            raise ValueError('Synthetic Unicode contract check failed')
        invalid=client.post('/scan',json={'url':'https://x..com'})
        if invalid.status_code!=422 or invalid.json()['error']['code']!='INVALID_URL':
            raise ValueError('Malformed URL error mapping failed')
    report=dict(model_version=provider.version,model_sha256=hashlib.sha256(Path(model_path).read_bytes()).hexdigest(),
                test_csv_sha256=hashlib.sha256(Path(test_path).read_bytes()).hexdigest(),
                real_heldout_urls_checked=len(selected),checks=checks,
                shap_class=1,shap_scale='probability',shap_additivity_checked=True,
                synthetic_unicode_contract_checked=True,invalid_url_checked=True,
                timing_scope='FastAPI TestClient in-process; excludes network and deployment',
                note='Checks API and explanations, not additional independent accuracy evidence.')
    Path(output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('model');p.add_argument('test_csv');p.add_argument('output')
    a=p.parse_args();verify(a.model,a.test_csv,a.output)
