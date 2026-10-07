"""Record a source-labeled fixture against live HTTP and standalone model output.

Input URL strings and detailed responses stay in the ignored output directory.
Do not treat application parity as classification accuracy or human sign-off.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from ml.integration import ModelProvider
from scripts.verify_application import request


def review(fixture,model,api,output):
    fixture,model,output=Path(fixture),Path(model),Path(output)
    if output.exists():raise ValueError('Choose a new review output directory')
    with fixture.open(encoding='utf-8',newline='') as file:rows=list(csv.DictReader(file))
    provider=ModelProvider(model);results=[];detailed=[]
    status,health=request(api,'/health')
    assert status==200 and health['ready'] and health['mode']=='model' and health['model_version']==provider.version
    for row in rows:
        status,actual=request(api,'/scan',{'url':row['url']})
        item=dict(id=row['id'],category=row['category'],http_status=status,
                  url_sha256=hashlib.sha256(row['url'].encode()).hexdigest(),source=row['source'] if row['category']!='benign' else 'Reviewed official publisher page')
        if row['category']=='malformed':
            assert status==422 and actual['error']['code'] in ('INVALID_URL','INVALID_REQUEST')
            item.update(application_pass=True,error_code=actual['error']['code'])
        else:
            assert status==200 and actual['mode']=='model' and actual['model_version']==provider.version
            prediction=provider.predict(row['url']);explanation=provider.explain(prediction)
            assert abs(actual['phishing_probability']-prediction.phishing_probability)<1e-12
            assert actual['normalized_host']==prediction.normalized_host
            assert actual['explanation_status']=='available' and actual['explanation_scale']=='probability'
            assert len(actual['explanation_items'])==len(explanation.items)
            for a,b in zip(actual['explanation_items'],explanation.items):
                assert a['feature']==b.feature and a['observed_value']==b.observed_value and abs(a['contribution']-b.contribution)<1e-12
            label=int(row['label']) if row['label']!='' else None
            item.update(application_pass=True,risk_score=actual['risk_score'],risk_level=actual['risk_level'],
                standalone_probability_match=True,shap_match=True,label=label,
                label_disagreement=((actual['phishing_probability']>=.5)!=bool(label)) if label is not None else None)
        results.append(item);detailed.append(dict(case=row,response=actual))
    output.mkdir(parents=True)
    report=dict(model_version=provider.version,model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),
        fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),reviewer='Codex assistant; no human teammate sign-off',
        scope='Local HTTP application parity; 12 source-labeled examples are too few for an accuracy benchmark',checks=results)
    (output/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (output/'detailed-private.json').write_text(json.dumps(detailed,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'application_cases':len(results),'label_disagreements':sum(r.get('label_disagreement') is True for r in results),'model_version':provider.version},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture',required=True);parser.add_argument('--model',required=True)
    parser.add_argument('--api',default='http://127.0.0.1:8000');parser.add_argument('--output',required=True)
    args=parser.parse_args();review(args.fixture,args.model,args.api,args.output)
