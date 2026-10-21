"""Package frozen research artifacts privately; weights and datasets stay out of Git."""
import hashlib
import json
from pathlib import Path
import zipfile

root=Path('artifacts/neural-run01')
required=['charcnn.pt','cnn-metadata.json','cascade-policy.json','evaluation.json','pre-evaluation.json']
paths=[root/name for name in required]
paths += [Path('ml/requirements-neural.txt'),Path('ml/requirements-verified.txt'),Path('docs/person1-neural-handoff.md')]
paths += [Path('data/processed/neural-holdout01/manifest.json')]
checksums={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
out=Path('artifacts/handoff/PhishX_neural_research_v1.zip');out.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for path in paths:z.write(path,str(path))
    z.writestr('SHA256SUMS.json',json.dumps(checksums,indent=2)+'\n')
print(str(out))

# Exact research inputs are a separate private archive, never part of Git.
holdout=Path('data/processed/neural-holdout01')
manifest=json.loads((holdout/'manifest.json').read_text())
snapshot_paths=[Path(p) for p in manifest['exclusion_inputs_sha256']]
for path in snapshot_paths:
    if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['exclusion_inputs_sha256'][str(path)]:
        raise ValueError('An original exclusion input changed: '+str(path))
snapshot_paths += [Path('data/raw/phiusiil.zip'),holdout/'holdout.csv',holdout/'manifest.json']
snapshot_checks={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in snapshot_paths}
snapshot=Path('artifacts/handoff/PhishX_neural_snapshots_v1.zip')
with zipfile.ZipFile(snapshot,'w',zipfile.ZIP_DEFLATED) as z:
    for path in snapshot_paths:z.write(path,str(path))
    z.writestr('SHA256SUMS.json',json.dumps(snapshot_checks,indent=2)+'\n')
print(str(snapshot))
