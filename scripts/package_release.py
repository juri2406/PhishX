"""Package the trusted passing local demo weights; never add the ZIP to Git."""
import hashlib,json,zipfile
from pathlib import Path
from phishx.release import validate_release_report
root=Path('artifacts/release-v7')
validate_release_report(json.loads((root/'release-evaluation.json').read_text()))
names=('classical.joblib','charcnn.pt','cnn-metadata.json','fusion.joblib','rank-context.joblib','cascade-policy.json','release-evaluation.json')
paths=[root/n for n in names]
manifest={'version':json.loads((root/'cascade-policy.json').read_text())['version'],'files':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'scope':'Trusted private local academic demo handoff; weights and frozen ranking context excluded from Git.'}
Path('docs/evidence/completion/release-v7-artifacts.json').write_text(json.dumps(manifest,indent=2)+'\n')
out=Path('artifacts/handoff/PhishX_release_v7_local_demo.zip');out.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for p in paths:z.write(p,str(p))
 for p in (Path('docs/evidence/completion/release-v7-artifacts.json'),Path('deploy/README.md'),Path('docs/project-completion.md')):z.write(p,str(p))
print(out)
