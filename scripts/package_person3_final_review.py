"""Package the actual final review; private source URL strings never enter Git."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

private=Path('work/person3-final')
files=[private/name for name in ('cases.json','fixture.csv','manifest.json','source-review.json','ui-observations.json','browser-classical-private.json','browser-cascade-private.json','http-review/summary.json','http-review/detailed-private.json')]
files += [Path('docs')/name for name in ('person3-final-review.md','person3-final-user-guide.pdf','person3-final-fixture-results.csv')]
files += sorted(Path('docs/evidence/person3-final').glob('*'))
for path in files:
    if not path.is_file():raise FileNotFoundError(path)
checks={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
out=Path('artifacts/handoff/PhishX_person3_final_review.zip');out.parent.mkdir(parents=True,exist_ok=True)
with ZipFile(out,'w',ZIP_DEFLATED) as archive:
    for path in files:archive.write(path,str(path))
    archive.writestr('SHA256SUMS.json',json.dumps(checks,indent=2)+'\n')
with ZipFile(out) as archive:
    assert all(hashlib.sha256(archive.read(path)).hexdigest()==digest for path,digest in checks.items())
print(str(out),'-',len(files),'files verified')
