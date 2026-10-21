"""Freeze a new external-domain cohort before release-policy evaluation."""
import bz2,csv,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
from phishx.urls import normalize_url,InvalidURL
from phishx.dataset import domain_skeleton

out=Path('data/processed/completion-external04')
if out.exists():raise ValueError('Choose a new version; do not overwrite a holdout')
prior=set()
inputs=list(Path('data/processed').rglob('*.csv'))+[Path('data/raw/uci_sample.csv'),Path('data/raw/uci_fresh_test.csv'),Path('work/person3/fixture.csv'),Path('work/person3-final/fixture.csv')]
for p in inputs:
    if p.exists():
        for r in csv.DictReader(p.open(encoding='utf-8-sig')):
            try:prior.add(domain_skeleton(normalize_url(r['url']).registrable_domain))
            except (InvalidURL,KeyError):pass
navigation=Path('data/raw/completion-navigation-v4-20261021.csv')
manifest=json.loads(navigation.with_suffix('.sources.json').read_text())
assert hashlib.sha256(navigation.read_bytes()).hexdigest()==manifest['input_sha256']
eligible={source['seed'] for source in manifest['sources'] if source.get('status')==200 and source.get('title') and not any(term in source['title'].lower() for term in ('coming soon','just a moment','access denied','404','redirect'))}
by_group={}
for row in csv.DictReader(navigation.open(encoding='utf-8')):
    if row['source'].removeprefix('official-navigation:') not in eligible:continue
    parsed=normalize_url(row['url']);group=domain_skeleton(parsed.registrable_domain)
    if group in prior:continue
    by_group.setdefault(group,[]).append(row)
rows=[];benign_groups=[]
# First 20 successful source groups in lexical group order; up to 10 paths each.
for group,candidates in sorted(by_group.items())[:20]:
    candidates.sort(key=lambda r:hashlib.sha256(('completion-external04:'+r['url']).encode()).hexdigest())
    for row in candidates[:10]:rows.append({'url':row['url'],'label':0,'group':group,'source':row['source']})
    benign_groups.append(group)
if len(benign_groups)<16:raise ValueError('Need at least 16 fresh benign source groups')
feed=Path('data/raw/phishtank-20261007.json.bz2')
assert hashlib.sha256(feed.read_bytes()).hexdigest()=='f9217d6eb4e455fc21e1a84af270bc3c9c16827db9e8f154971835f64b6ce593'
records=json.loads(bz2.decompress(feed.read_bytes()));seen=set(benign_groups);phishing=0
for r in sorted(records,key=lambda r:hashlib.sha256(('completion-external04:'+str(r['phish_id'])).encode()).hexdigest()):
    if r.get('verified')!='yes' or r.get('online')!='yes':continue
    try:group=domain_skeleton(normalize_url(r['url']).registrable_domain)
    except InvalidURL:continue
    if group in prior or group in seen:continue
    seen.add(group);rows.append({'url':r['url'],'label':1,'group':group,'source':'phishtank:id-'+str(r['phish_id'])});phishing+=1
    if phishing==200:break
assert phishing==200 and not seen&prior
out.mkdir(parents=True)
with (out/'holdout.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['url','label','group','source']);w.writeheader();w.writerows(rows)
public={'frozen_at':datetime.now(timezone.utc).isoformat(),'rows':len(rows),'benign_rows':len(rows)-phishing,'phishing_rows':phishing,
        'benign_groups':len(benign_groups),'phishing_groups':phishing,'prior_group_count':len(prior),'prior_group_overlap':0,
        'holdout_sha256':hashlib.sha256((out/'holdout.csv').read_bytes()).hexdigest(),'navigation_sha256':manifest['input_sha256'],
        'feed_sha256':hashlib.sha256(feed.read_bytes()).hexdigest(),
        'policy':'Fixed hash sampling before predictions; max 10 official navigation paths per unused domain; one historical source-labelled phishing URL per unused domain. No outcome-based replacement.',
        'limitations':'Convenience technical-publisher benign pages and historical PhishTank labels, not a population-prevalence or forward-temporal test.'}
(out/'manifest.json').write_text(json.dumps(public,indent=2)+'\n');print(json.dumps(public,indent=2))
