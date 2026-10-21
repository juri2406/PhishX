"""Freeze expanded development pool; prior inspected tests are development only."""
import csv,hashlib,json
from pathlib import Path
from phishx.urls import normalize_url,InvalidURL
from phishx.dataset import domain_skeleton
out=Path('data/processed/release-v7')
if out.exists():raise ValueError('Choose a new revision')
inputs=[Path('data/processed/release-v4/test.csv')]
inputs+=sorted(Path('data/processed').glob('completion-*/holdout.csv'))
inputs+=sorted(Path('data/raw').glob('*navigation*.csv'))
records={};labels={}
for p in inputs:
 for r in csv.DictReader(p.open(encoding='utf-8-sig')):
  if r.get('label') not in ('0','1'):continue
  try:n=normalize_url(r['url'])
  except InvalidURL:continue
  key=n.canonical;label=int(r['label']);labels.setdefault(key,set()).add(label)
  records[(key,label)]={'url':key,'label':label,'group':domain_skeleton(n.registrable_domain),'source':r.get('source','development')}
rows=[r for (key,label),r in records.items() if len(labels[key])==1]
out.mkdir(parents=True)
with (out/'development.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['url','label','group','source']);w.writeheader();w.writerows(rows)
manifest={'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'rows':len(rows),'conflicting_urls_removed':sum(len(v)>1 for v in labels.values()),'sha256':hashlib.sha256((out/'development.csv').read_bytes()).hexdigest()}
(out/'development-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({k:v for k,v in manifest.items() if k!='inputs'}))
