"""Package ignored model/snapshot handoffs and source-labeled review candidates."""
import csv
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from phishx.model import load_rows, load_bundle
from phishx.urls import normalize_url


def package():
    root=Path('artifacts/handoff');root.mkdir(parents=True,exist_ok=True)
    artifact=Path('artifacts/revised-run06/classical.joblib')
    bundle=load_bundle(artifact)
    evaluation=json.loads(Path('docs/evidence/person1/revised-model-results.json').read_text())
    digest=hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert evaluation['artifact_sha256']==digest
    metadata={k:v for k,v in bundle.items() if k!='model'}
    metadata['artifact_sha256']=digest
    (root/'run06-model-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    (root/'run06-sha256.txt').write_text(digest+'  artifacts/revised-run06/classical.joblib\n')
    paths=[artifact,root/'run06-model-metadata.json',root/'run06-sha256.txt',Path('ml/requirements-verified.txt'),Path('backend/requirements-model.txt')]
    paths += [Path('docs')/name for name in ('model-handoff.md','person1-handoff.md','person1-revised-workflow.md','person1-vscode.md','person1-setup.md','evaluation-run06.md')]
    paths += sorted(Path('docs/evidence/person1').glob('*.json'))
    with ZipFile(root/'PhishX_model_handoff_v6.zip','w',ZIP_DEFLATED) as archive:
        for path in paths:archive.write(path,str(path))
    # Separate reproducibility snapshot: private handoff, never add to Git.
    snapshots=[Path('data/raw')/name for name in ('uci_sample.csv','uci_fresh_test.csv','phishtank-20261007.json.bz2')]
    snapshots += sorted(Path('data/raw').glob('official-navigation*.csv'))
    snapshots += sorted(Path('data/raw').glob('official-navigation*.sources.json'))
    snapshots += [Path('data/processed/uci-run02')/name for name in ('train.csv','validation.csv','manifest.json')]
    checksums={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in snapshots}
    (root/'snapshot-sha256.json').write_text(json.dumps(checksums,indent=2)+'\n')
    with ZipFile(root/'PhishX_research_snapshots_v6.zip','w',ZIP_DEFLATED) as archive:
        for path in snapshots+[root/'snapshot-sha256.json']:archive.write(path,str(path))
    rows=load_rows('data/processed/revised-run06/final.csv');selected=[]
    for label in ('0','1'):
        seen=set()
        for row in rows:
            if row['label']!=label or row['actual_domain'] in seen:continue
            seen.add(row['actual_domain']);selected.append(row)
            if len(seen)==6:break
    cases=[]
    for row in selected:
        cases.append(dict(category='benign' if row['label']=='0' else 'phishing',url=row['url'],provenance=row['source'],
            label_basis='Owning-domain navigation candidate; individual page not independently certified' if row['label']=='0' else 'PhishTank verified=yes online=yes in 2026-10-07 snapshot; source verification '+row['collected_at'],
            expected_behavior='HTTP 200; actual model output and explanation; record disagreement with source label'))
    for url in ('https://pаypal.com/login','https://gооgle.com/','https://аpple.com/','https://micrоsoft.com/'):
        normalize_url(url)
        cases.append(dict(category='synthetic_homoglyph',url=url,provenance='Offline generated string; no page fetched',label_basis='Synthetic impersonation intent, not live verified phishing',expected_behavior='HTTP 200; source Unicode/brand signals and actual model output; no forced score'))
    for url in ('ftp://example.org','https://x..com','https://example.org/%GG','https://example.org/a b'):
        cases.append(dict(category='malformed',url=url,provenance='Developer-created invalid input',label_basis='Protocol/host/encoding/whitespace invalid',expected_behavior='HTTP 422 with structured INVALID_URL or VALIDATION_ERROR'))
    fields=['case_id','category','url','provenance','label_basis','expected_behavior','actual_result','pass_fail','notes']
    with (root/'person3-review-v6.csv').open('w',newline='',encoding='utf-8') as file:
        writer=csv.DictWriter(file,fieldnames=fields);writer.writeheader()
        writer.writerows(dict(case_id=i,**row,actual_result='',pass_fail='',notes='Developer source package, not independent review') for i,row in enumerate(cases,1))
    print(json.dumps({'model_version':bundle['version'],'model_sha256':digest,'review_rows':len(cases),'outputs':[str(root/name) for name in ('PhishX_model_handoff_v6.zip','PhishX_research_snapshots_v6.zip','person3-review-v6.csv')]},indent=2))


if __name__=='__main__': package()
