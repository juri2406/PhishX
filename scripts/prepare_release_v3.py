"""All previously inspected cohorts become development data; new splits by group."""
import bz2,csv,hashlib,json
from pathlib import Path
from phishx.urls import normalize_url,InvalidURL
from phishx.dataset import prepare,domain_skeleton

out=Path('data/processed/release-v3')
if out.exists():raise ValueError('Use a new revision')
inputs=list(Path('data/processed').rglob('*.csv'))+[Path('data/raw/uci_sample.csv'),Path('data/raw/uci_fresh_test.csv'),Path('data/raw/completion-navigation-20261021.csv'),Path('work/person3/fixture.csv'),Path('work/person3-final/fixture.csv')]
records=[];seen=set()
for p in inputs:
    if not p.exists():continue
    for r in csv.DictReader(p.open(encoding='utf-8-sig')):
        if r.get('label') not in ('0','1'):continue
        try:parsed=normalize_url(r['url'])
        except (InvalidURL,KeyError):continue
        source=r.get('source','development-snapshot')
        records.append(dict(url=parsed.canonical,label=r['label'],source=source,collected_at=r.get('collected_at','historical'),group_domain='',family='original'))
        seen.add(domain_skeleton(parsed.registrable_domain))
feed=json.loads(bz2.decompress(Path('data/raw/phishtank-20261007.json.bz2').read_bytes()))
added=0
for r in sorted(feed,key=lambda r:hashlib.sha256(('release-v3-training:'+str(r['phish_id'])).encode()).hexdigest()):
    if r.get('verified')!='yes' or r.get('online')!='yes':continue
    try:p=normalize_url(r['url']);group=domain_skeleton(p.registrable_domain)
    except InvalidURL:continue
    if group in seen:continue
    records.append(dict(url=p.canonical,label=1,source='phishtank:release-v3',collected_at=r['verification_time'],group_domain='',family='original'))
    seen.add(group);added+=1
    if added==5000:break
raw=Path('data/raw/release-v3-development.csv')
with raw.open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
manifest=prepare(raw,out,seed=20261022)
print(json.dumps({'added_phishing_groups':added,'input_rows':len(records),'input_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'policy':'All earlier holdouts are development now; never reuse as fresh evidence. Exact connected-group deduplication/splitting uses the shared dataset pipeline.'},indent=2))
