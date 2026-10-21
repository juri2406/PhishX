"""Freeze the predeclared consensus policy, then evaluate fresh held-out cohorts."""
import hashlib,json,shutil
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import torch
from phishx.cascade import CascadePredictor
from phishx.model import load_rows,probability_report

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
out=Path('artifacts/completion-cascade02')
if out.exists():raise ValueError('Use a new candidate directory; never overwrite inspected results')
plan_path=Path('work/completion/release-plan.json');plan=json.loads(plan_path.read_text())
cohorts={'fresh_uci':'data/processed/completion-uci02','fresh_external':'data/processed/completion-external02'}
seals={name:json.loads((Path(p)/'manifest.json').read_text()) for name,p in cohorts.items()}
for name,p in cohorts.items():assert digest(Path(p)/'holdout.csv')==seals[name].get('holdout_sha256')
out.mkdir(parents=True)
for name in ('charcnn.pt','cnn-metadata.json'):shutil.copy2(Path('artifacts/neural-run01')/name,out/name)
policy={'lower':.5,'upper':.9,'cnn_weight':1.,'fusion':'minimum','classical_sha256':digest('artifacts/revised-run06/classical.joblib'),
        'cnn_version':json.loads((out/'cnn-metadata.json').read_text())['version'],'probability_calibrated':False,
        'cascade_code_sha256':digest('ml/phishx/cascade.py'),'explanation_code_sha256':digest('ml/phishx/component_shapley.py'),
        'policy':'Uncertain positive confirmation: RF outside inclusive [.5,.9] is unchanged; inside, min(RF,CNN). Neural scores never raise the classical score.',
        'quality_plan_sha256':digest(plan_path)}
policy['version']='consensus-v2-'+hashlib.sha256(json.dumps(policy,sort_keys=True).encode()).hexdigest()[:12]
(out/'cascade-policy.json').write_text(json.dumps(policy,indent=2)+'\n')
pre={'frozen_at':datetime.now(timezone.utc).isoformat(),'plan':plan,'policy':policy,'cohort_manifests':seals}
(out/'pre-evaluation.json').write_text(json.dumps(pre,indent=2)+'\n')
torch.set_num_threads(4);candidate=CascadePredictor(out,'artifacts/revised-run06/classical.joblib')
report=dict(pre,cohorts={})
for name,p in cohorts.items():
    rows=load_rows(Path(p)/'holdout.csv');urls=[r['url'] for r in rows];y=[int(r['label']) for r in rows]
    prob,rf,routed,_=candidate.predict(urls)
    assert np.all(prob<=rf+1e-7)
    report['cohorts'][name]={'rows':len(rows),'groups':len({r['group'] for r in rows}),'classical':probability_report(y,rf),
                           'consensus':probability_report(y,prob),'routed_fraction':float(routed.mean()),'scores_never_increased':True}
g=plan['quality_gates'];u=report['cohorts']['fresh_uci'];e=report['cohorts']['fresh_external']
checks={'uci_recall':u['consensus']['recall']>=g['uci_min_recall'],'uci_fpr':u['consensus']['false_positive_rate']<=g['uci_max_false_positive_rate'],
        'external_recall':e['consensus']['recall']>=g['external_min_recall'],'external_fpr':e['consensus']['false_positive_rate']<=g['external_max_false_positive_rate'],
        'recall_noninferiority':all(r['consensus']['recall']>=r['classical']['recall']-g['each_holdout_max_recall_drop_against_rf'] for r in report['cohorts'].values()),
        'fpr_did_not_worsen':all(r['consensus']['false_positive_rate']<=r['classical']['false_positive_rate'] for r in report['cohorts'].values())}
report['quality_checks']=checks;report['all_quality_gates_passed']=all(checks.values())
report['interpretation']='Local academic-demo release gates only; convenience-source, historical labels, uncalibrated scores. No production guarantee or population accuracy claim.'
(out/'release-evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'version':policy['version'],'cohorts':{name:{kind:{k:r[kind][k] for k in ('accuracy','recall','false_positive_rate','confusion_matrix')} for kind in ('classical','consensus')} for name,r in report['cohorts'].items()},'quality_checks':checks,'all_passed':report['all_quality_gates_passed']},indent=2))
