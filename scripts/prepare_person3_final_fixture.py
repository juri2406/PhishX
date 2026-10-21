"""Select a separate fixture before inspecting predictions; outputs stay ignored."""
import argparse
from pathlib import Path
import bz2,json,csv,hashlib
from collections import Counter
from phishx.urls import normalize_url,InvalidURL
from phishx.dataset import domain_skeleton
from phishx.model import load_rows
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',default='work/person3-final')
args=parser.parse_args()
root=Path(args.output)
if root.exists():raise ValueError('Choose a new fixture directory; do not overwrite a reviewed fixture')
assert hashlib.sha256(Path('artifacts/revised-run06/classical.joblib').read_bytes()).hexdigest()=='a5a68744712975f0f5809dd6f13825eeb47dc4251153f3f65eadc2120727d3ed'
assert hashlib.sha256(Path('data/raw/phishtank-20261007.json.bz2').read_bytes()).hexdigest()=='f9217d6eb4e455fc21e1a84af270bc3c9c16827db9e8f154971835f64b6ce593'
benign=['https://haxe.org/manual/','https://mariadb.org/documentation/','https://fishshell.com/docs/current/','https://alpinelinux.org/about/','https://crystal-lang.org/','https://gleam.run/documentation/']
prior=set()
for p in Path('data/processed').rglob('*.csv'):
    for r in load_rows(p):
        try:prior.add(domain_skeleton(normalize_url(r['url']).registrable_domain))
        except InvalidURL:pass
for p in ('data/raw/uci_sample.csv','data/raw/uci_fresh_test.csv','work/person3/fixture.csv'):
    for r in load_rows(p):
        try:prior.add(domain_skeleton(normalize_url(r['url']).registrable_domain))
        except InvalidURL:pass
for u in benign:
    assert domain_skeleton(normalize_url(u).registrable_domain) not in prior,u
feed=json.loads(bz2.decompress(Path('data/raw/phishtank-20261007.json.bz2').read_bytes()))
selected=[];seen=set()
for r in sorted(feed,key=lambda r:hashlib.sha256(('person3-final-independent:'+str(r['phish_id'])).encode()).hexdigest()):
    if r.get('verified')!='yes' or r.get('online')!='yes':continue
    try: group=domain_skeleton(normalize_url(r['url']).registrable_domain)
    except InvalidURL:continue
    if group in prior or group in seen:continue
    seen.add(group);selected.append(r)
    if len(selected)==6:break
assert len(selected)==6
cases=[dict(id=f'benign-{i+1}',category='benign',url=u,label=0,source=u,label_basis='Official publisher/organization page; page title and response checked separately') for i,u in enumerate(benign)]
cases += [dict(id=f'phishing-{i+1}',category='phishing',url=r['url'],label=1,source='phishtank:id-'+str(r['phish_id']),label_basis='Source verified=yes and online=yes in October snapshot; verification '+r['verification_time']) for i,r in enumerate(selected)]
cases += [dict(id=f'synthetic-{i+1}',category='synthetic_homoglyph',url=u,label='',source='Offline generated Unicode string',label_basis='Synthetic brand impersonation intent; not a live verified phishing page') for i,u in enumerate(['https://аpple.example/account','https://аmazon.example/signin','https://microsоft.example/login','https://gооgle.example/verify'])]
cases += [dict(id=f'invalid-{i+1}',category='malformed',url=u,label='',source='Developer invalid input',label_basis='Invalid scheme/host/percent encoding/whitespace') for i,u in enumerate(['javascript:alert(1)','https://bad..example/','https://example.org/%ZZ','https://example.org/with space'])]
root.mkdir(parents=True)
(root/'cases.json').write_text(json.dumps(cases,indent=2)+'\n',encoding='utf-8')
with (root/'fixture.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(cases[0]));w.writeheader();w.writerows(cases)
print(json.dumps({'counts':dict(Counter(c['category'] for c in cases)),'real_domain_skeleton_overlap':0,'phishing_verification_dates':[r['verification_time'] for r in selected]},indent=2))

manifest={'counts':dict(Counter(c['category'] for c in cases)), 'real_domain_skeleton_overlap':0,'selection_policy':'Fixed before predictions; official publisher candidates and hash-sampled unused PhishTank domain groups; no outcome-based substitutions.', 'excludes':'All processed CSVs including frozen neural holdout, both observed UCI samples and original Person 3 fixture', 'prior_group_count':len(prior), 'fixture_sha256':hashlib.sha256((root/'fixture.csv').read_bytes()).hexdigest(), 'feed_sha256':hashlib.sha256(Path('data/raw/phishtank-20261007.json.bz2').read_bytes()).hexdigest(), 'neural_weights_sha256':hashlib.sha256(Path('artifacts/neural-run01/charcnn.pt').read_bytes()).hexdigest(), 'phishing_verification_dates':[r['verification_time'] for r in selected]}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
