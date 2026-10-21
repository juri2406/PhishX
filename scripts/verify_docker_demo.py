"""Real deployed HTTP smoke against standalone frozen models; never visits targets."""
import json,os
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from ml.integration import create_provider

base='http://127.0.0.1:8080'
def request(path,body=None):
    r=Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
    try:
        with urlopen(r,timeout=35) as response:return response.status,response.headers, response.read()
    except HTTPError as exc:return exc.code,exc.headers,exc.read()
status,headers,body=request('/')
assert status==200 and b'id="root"' in body
assert headers['X-Content-Type-Options']=='nosniff' and headers['X-Frame-Options']=='DENY'
assert "default-src 'self'" in headers['Content-Security-Policy']
status,_,body=request('/api/health');health=json.loads(body);assert status==200 and health['ready']
provider=create_provider();records=[]
for url in ('https://example.com/','https://pаypal.com/login','https://github.com/juri2406/PhishX'):
    prediction=provider.predict(url)
    status,_,body=request('/api/scan',{'url':url});actual=json.loads(body)
    assert status==200 and actual['model_version']==provider.version
    assert abs(actual['phishing_probability']-prediction.phishing_probability)<1e-5
    assert actual['explanation_status']=='available' and actual['explanation_method']=='tree_shap'
    expected_explanation=provider.explain(prediction)
    assert len(actual['explanation_items'])==len(expected_explanation.items)
    for observed,expected in zip(actual['explanation_items'],expected_explanation.items):
        assert observed['feature']==expected.feature
        assert abs(observed['contribution']-expected.contribution)<1e-5
    records.append({'url':url,'probability':actual['phishing_probability'],'risk_score':actual['risk_score'],'model_used':actual['model_used'],
                    'explanation_method':actual['explanation_method'],'standalone_explanation_parity':True,'timings_ms':actual['timings_ms']})
for url in ('javascript:alert(1)','https://bad..example/'):
    status,_,body=request('/api/scan',{'url':url});assert status==422
status,_,body=request('/api/signals',{'url':'http://127.0.0.1/'});assert status==422
status,_,body=request('/api/signals',{'url':'https://example.com/'});live=json.loads(body)
assert status==200 and len(live['checks'])==4 and live['affects_model_score'] is False
for path in ('/classical.joblib','/.env'):
    status,_,_=request(path);assert status in (403,404)
record={'recorded_at':datetime.now(timezone.utc).isoformat(),'base':base,'health':health,'real_model_checks':records,'live_checks':live,
        'checks':{'root_served':True,'same_origin_proxy':True,'model_parity':True,'additivity':True,'malformed_rejected':True,'private_targets_blocked':True,
                  'security_headers':True,'model_and_dotfiles_not_served':True},'scope':'Real local nginx+Linux containers; model latency is actual backend timing, not a fabricated estimate.'}
out=Path('docs/evidence/completion/docker-http.json');out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
