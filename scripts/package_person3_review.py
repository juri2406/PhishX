"""Bundle recorded review material; raw fixture URLs stay outside Git."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root=Path('artifacts/handoff');root.mkdir(parents=True,exist_ok=True)
files=[root/'person3-final-fixture.csv',Path('work/person3/fixture.csv'),
    Path('work/person3/cases.json'),Path('work/person3/browser-results.json'),
    Path('work/person3/http-review/detailed-private.json')]
files += [Path('docs')/name for name in ('person3-user-guide.pdf','person3-review.md',
    'person23-acceptance.md','milestone-acceptance.md','person3-fixture-results.csv')]
files += sorted(Path('docs/evidence/person3').glob('*'))
for path in files:
    if not path.is_file():raise FileNotFoundError(path)
with ZipFile(root/'PhishX_person3_review_v6.zip','w',ZIP_DEFLATED) as archive:
    for path in files:archive.write(path,str(path))
    archive.writestr('artifacts/handoff/person3-file-checksums.json',json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
print(root/'PhishX_person3_review_v6.zip')
