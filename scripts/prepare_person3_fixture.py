"""Select a separate fixture before inspecting predictions; outputs stay ignored."""
import argparse
from pathlib import Path
import bz2,json,csv,hashlib
from collections import Counter
from phishx.urls import normalize_url,InvalidURL
from phishx.dataset import domain_skeleton
from phishx.model import load_rows
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',default='work/person3')
args=parser.parse_args()
root=Path(args.output)
if root.exists():raise ValueError('Choose a new fixture directory; do not overwrite a reviewed fixture')
assert hashlib.sha256(Path('artifacts/revised-run06/classical.joblib').read_bytes()).hexdigest()=='a5a68744712975f0f5809dd6f13825eeb47dc4251153f3f65eadc2120727d3ed'
assert hashlib.sha256(Path('data/raw/phishtank-20261007.json.bz2').read_bytes()).hexdigest()=='f9217d6eb4e455fc21e1a84af270bc3c9c16827db9e8f154971835f64b6ce593'
benign=['https://svelte.dev/docs/svelte/overview','https://www.typescriptlang.org/docs/','https://www.solidjs.com/','https://v2.tauri.app/start/','https://ziglang.org/learn/','https://nim-lang.org/documentation.html']
prior=set()
for p in Path('data/processed').rglob('*.csv'):
    for r in load_rows(p):
        try:prior.add(domain_skeleton(normalize_url(r['url']).registrable_domain))
        except InvalidURL:pass
for p in ('data/raw/uci_sample.csv','data/raw/uci_fresh_test.csv'):
    for r in load_rows(p):
        try:prior.add(domain_skeleton(normalize_url(r['url']).registrable_domain))
        except InvalidURL:pass
for u in benign:
    assert domain_skeleton(normalize_url(u).registrable_domain) not in prior,u
feed=json.loads(bz2.decompress(Path('data/raw/phishtank-20261007.json.bz2').read_bytes()))
selected=[];seen=set()
for r in sorted(feed,key=lambda r:hashlib.sha256(('person3-independent:'+str(r['phish_id'])).encode()).hexdigest()):
    if r.get('verified')!='yes' or r.get('online')!='yes':continue
    try: group=domain_skeleton(normalize_url(r['url']).registrable_domain)
    except InvalidURL:continue
    if group in prior or group in seen:continue
    seen.add(group);selected.append(r)
    if len(selected)==6:break
assert len(selected)==6
cases=[dict(id=f'benign-{i+1}',category='benign',url=u,label=0,source=u,label_basis='Official language/framework publisher documentation; page title and response checked separately') for i,u in enumerate(benign)]
cases += [dict(id=f'phishing-{i+1}',category='phishing',url=r['url'],label=1,source='phishtank:id-'+str(r['phish_id']),label_basis='Source verified=yes and online=yes in October snapshot; verification '+r['verification_time']) for i,r in enumerate(selected)]
cases += [dict(id=f'synthetic-{i+1}',category='synthetic_homoglyph',url=u,label='',source='Offline generated Unicode string',label_basis='Synthetic brand impersonation intent; not a live verified phishing page') for i,u in enumerate(['https://drоpbox.example/','https://аdobe.example/','https://nеtflix.example/','https://linkedіn.example/'])]
cases += [dict(id=f'invalid-{i+1}',category='malformed',url=u,label='',source='Developer invalid input',label_basis='Invalid scheme/host/percent encoding/whitespace') for i,u in enumerate(['file:///tmp/test','https://bad..example','https://example.org/%GG','https://example.org/a b'])]
root.mkdir(parents=True)
(root/'cases.json').write_text(json.dumps(cases,indent=2)+'\n',encoding='utf-8')
with (root/'fixture.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(cases[0]));w.writeheader();w.writerows(cases)
print(json.dumps({'counts':dict(Counter(c['category'] for c in cases)),'real_domain_skeleton_overlap':0,'phishing_verification_dates':[r['verification_time'] for r in selected]},indent=2))
