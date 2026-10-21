"""Run independently frozen fixtures against real classical and cascade HTTP APIs."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from ml.integration import ModelProvider
from ml.neural_integration import CascadeProvider
from scripts.verify_application import request


def review(fixture, output, classical_api, cascade_api):
    fixture,output=Path(fixture),Path(output)
    if output.exists():raise ValueError('Choose new review output')
    cases=list(csv.DictReader(fixture.open(encoding='utf-8',newline='')))
    providers={'classical':ModelProvider('artifacts/revised-run06/classical.joblib'),
               'cascade':CascadeProvider('artifacts/neural-run01','artifacts/revised-run06/classical.joblib')}
    results={};details={}
    for name,provider in providers.items():
        api=classical_api if name=='classical' else cascade_api
        status,health=request(api,'/health')
        assert status==200 and health['ready'] and health['model_version']==provider.version
        observations=[];private=[]
        for case in cases:
            status,data=request(api,'/scan',{'url':case['url']})
            item={'id':case['id'],'category':case['category'],'url_sha256':hashlib.sha256(case['url'].encode()).hexdigest(),
                  'http_status':status,'source':case['source'] if case['category']!='benign' else 'Reviewed official publisher page'}
            if case['category']=='malformed':
                assert status==422 and data['error']['code'] in {'INVALID_URL','INVALID_REQUEST'}
                item.update(application_pass=True,error_code=data['error']['code'])
            else:
                expected=provider.predict(case['url'])
                assert status==200 and data['mode']=='model' and data['model_version']==provider.version
                assert abs(data['phishing_probability']-expected.phishing_probability)<1e-6
                assert data['normalized_host']==expected.normalized_host
                assert data['model_used']==expected.context.get('model_used','classical')
                if expected.context.get('cnn_routed'):
                    assert data['explanation_status']=='unavailable' and data['explanation_items']==[]
                else:
                    explanation=provider.explain(expected)
                    assert data['explanation_status']=='available' and data['explanation_scale']==explanation.scale
                    assert len(data['explanation_items'])==len(explanation.items)
                    for actual,item_expected in zip(data['explanation_items'],explanation.items):
                        assert actual['feature']==item_expected.feature and abs(actual['contribution']-item_expected.contribution)<1e-9
                label=int(case['label']) if case['label'] else None
                item.update(application_pass=True,probability=data['phishing_probability'],risk_score=data['risk_score'],risk_level=data['risk_level'],
                            model_used=data['model_used'],explanation_status=data['explanation_status'],label=label,
                            label_disagreement=((data['phishing_probability']>=.5)!=bool(label)) if label is not None else None)
            observations.append(item);private.append({'case':case,'response':data})
        results[name]={'health':health,'checks':observations,'application_passes':sum(x['application_pass'] for x in observations),
                       'benign_false_positives':sum(x.get('label')==0 and x.get('label_disagreement') is True for x in observations),
                       'phishing_misses':sum(x.get('label')==1 and x.get('label_disagreement') is True for x in observations)}
        details[name]=private
    output.mkdir(parents=True)
    summary={'reviewer':'Codex assistant; no separate human sign-off','fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),
             'scope':'Application/standalone parity and small source-labeled regression review, not a representative accuracy benchmark','models':results}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (output/'detailed-private.json').write_text(json.dumps(details,indent=2)+'\n')
    print(json.dumps({name:{k:v for k,v in r.items() if k not in ('health','checks')} for name,r in results.items()},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixture',required=True);p.add_argument('--output',required=True)
    p.add_argument('--classical-api',default='http://127.0.0.1:8000');p.add_argument('--cascade-api',default='http://127.0.0.1:8001')
    a=p.parse_args();review(a.fixture,a.output,a.classical_api,a.cascade_api)
