"""Verify browser/HTTP/standalone agreement and publish only redacted evidence."""
import csv
import hashlib
import json
from pathlib import Path

root=Path('work/person3-final');out=Path('docs/evidence/person3-final');out.mkdir(parents=True,exist_ok=True)
summary=json.loads((root/'http-review/summary.json').read_text())
private=json.loads((root/'http-review/detailed-private.json').read_text())
for name in ('classical','cascade'):
    browser=json.loads((root/f'browser-{name}-private.json').read_text())
    assert len(browser)==len(private[name])==20
    for b,h in zip(browser,private[name]):
        assert b['id']==h['case']['id']
        if h['case']['category']=='malformed':
            assert b['error']==h['response']['error']['message']
        else:
            for key in ('risk_score','risk_level','normalized_host','model_used','cascade_status','explanation_status'):
                assert b['response'][key]==h['response'][key]
            assert abs(b['response']['phishing_probability']-h['response']['phishing_probability'])<1e-6
            assert b['response']['explanation_items']==h['response']['explanation_items']
    summary['models'][name]['browser_application_passes']=20
    for case in summary['models'][name]['checks']:case['browser_parity_pass']=True
(out/'fixture-results.json').write_text(json.dumps(summary,indent=2)+'\n')
for filename in ('manifest.json','source-review.json','ui-observations.json'):
    (out/filename).write_bytes((root/filename).read_bytes())
rows=[]
for name,model in summary['models'].items():
    for case in model['checks']:rows.append({'model':name,**case})
fields=list(dict.fromkeys(key for row in rows for key in row))
with Path('docs/person3-final-fixture-results.csv').open('w',encoding='utf-8',newline='') as file:
    writer=csv.DictWriter(file,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)
print('Verified 40 browser/HTTP/standalone cases; published redacted summaries.')
