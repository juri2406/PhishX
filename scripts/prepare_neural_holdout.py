"""Freeze unused UCI groups before training; no predictions or outcome selection."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile
from phishx.urls import normalize_url, InvalidURL
from phishx.dataset import domain_skeleton


def prepare(output, per_class=1000):
    output = Path(output)
    if output.exists(): raise ValueError('Use a new output directory')
    observed = set()
    inputs = sorted(Path('data/processed').glob('**/*.csv')) + [Path('data/raw/uci_sample.csv'),Path('data/raw/uci_fresh_test.csv'),Path('work/person3/fixture.csv')]
    hashes = {}
    for path in inputs:
        if not path.exists(): continue
        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        with path.open(encoding='utf-8-sig',newline='') as file:
            for row in csv.DictReader(file):
                try: observed.add(domain_skeleton(normalize_url(row['url']).registrable_domain))
                except (InvalidURL,KeyError): pass
    archive = Path('data/raw/phiusiil.zip')
    if hashlib.sha256(archive.read_bytes()).hexdigest() != '0a639fd03aea6308c5b1c10c92aa23c2ce1505447a9137271865cd0badc9a59a':
        raise ValueError('UCI archive differs from the recorded source snapshot')
    with zipfile.ZipFile(archive) as z:
        with z.open('PhiUSIIL_Phishing_URL_Dataset.csv') as file:
            candidates = [(r['URL'],1-int(r['label'])) for r in csv.DictReader(io.TextIOWrapper(file,encoding='utf-8-sig'))]
    candidates.sort(key=lambda r:hashlib.sha256(('neural-holdout-v1:'+r[0]).encode()).hexdigest())
    rows = []; counts = {0:0,1:0}; selected = set()
    for url,label in candidates:
        if counts[label] >= per_class: continue
        try:
            parsed = normalize_url(url)
            group = domain_skeleton(parsed.registrable_domain)
        except InvalidURL: continue
        if group in observed or group in selected: continue
        selected.add(group); counts[label] += 1
        rows.append(dict(url=parsed.canonical,label=label,group=group,source='UCI-967-unused-original-archive'))
        if min(counts.values()) >= per_class: break
    if min(counts.values()) != per_class: raise ValueError(f'Insufficient unseen groups: {counts}')
    output.mkdir(parents=True)
    with (output/'holdout.csv').open('w',encoding='utf-8',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=['url','label','group','source']);writer.writeheader();writer.writerows(rows)
    manifest={'policy':'Frozen before neural training. SHA256 order, one record per unused registrable-domain skeleton; 1000 per class. UCI original label 1=benign inverted explicitly. No predictions used.',
              'limitation':'Historical same-source convenience sample, deliberately balanced; not live-web prevalence, external-source or temporal validation.',
              'rows':len(rows),'labels':counts,'observed_group_count':len(observed),'observed_overlap':len(selected&observed),
              'exclusion_inputs_sha256':hashes,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
              'holdout_sha256':hashlib.sha256((output/'holdout.csv').read_bytes()).hexdigest()}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='exclusion_inputs_sha256'},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output');a=p.parse_args();prepare(a.output)
