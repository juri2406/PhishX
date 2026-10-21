"""Held-out logistic fusion; preserve earlier failures and test only new cohorts."""
import hashlib,json,shutil
from pathlib import Path
from datetime import datetime,timezone
import joblib,numpy as np,torch
from sklearn.linear_model import LogisticRegression
from phishx.cascade import fusion_features
from phishx.charcnn import CNNPredictor
from phishx.model import load_bundle,load_rows,probability_report
from phishx.extended_features import analyze_extended

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def balanced(r):return (r['recall']+1-r['false_positive_rate'])/2
out=Path('artifacts/release-v5')
if out.exists():raise ValueError('Use a new revision')
cohorts={'fresh_uci':Path('data/processed/completion-uci05'),'fresh_external':Path('data/processed/completion-external05')}
seals={name:json.loads((p/'manifest.json').read_text()) for name,p in cohorts.items()}
for name,p in cohorts.items():assert digest(p/'holdout.csv')==seals[name]['holdout_sha256']
gates=json.loads(Path('work/completion/release-plan.json').read_text())['quality_gates']
torch.set_num_threads(4)
# v4's internal test split was not used for its weights or epoch/model selection.
cal=load_rows('data/processed/release-v4/test.csv')
fit=[r for r in cal if int(hashlib.sha256(('fusion-v5:'+r['group_domain']).encode()).hexdigest()[:8],16)%10<7]
review=[r for r in cal if int(hashlib.sha256(('fusion-v5:'+r['group_domain']).encode()).hexdigest()[:8],16)%10>=7]
assert not {r['group_domain'] for r in fit}&{r['group_domain'] for r in review}
bundle=load_bundle('artifacts/release-v4/classical.joblib');cnn=CNNPredictor('artifacts/release-v4')
def scores(rows):
    urls=[r['url'] for r in rows];features=[analyze_extended(u)['features'] for u in urls]
    rf=bundle['model'].predict_proba([[f[k] for k in bundle['feature_names']] for f in features])[:,1]
    return rf,np.array(cnn.probabilities(urls))
xs={};ys={}
for name,rows in [('fit',fit),('review',review)]:
    rf,nn=scores(rows);xs[name]=fusion_features(rf,nn);ys[name]=[int(r['label']) for r in rows]
candidates=[]
for weight in (1.,3.,10.,20.):
    model=LogisticRegression(C=1.,max_iter=2000,random_state=42).fit(xs['fit'],ys['fit'],sample_weight=[weight if r['source'].startswith('official-navigation:') else 1. for r in fit])
    report=probability_report(ys['review'],model.predict_proba(xs['review'])[:,1]);candidates.append((model,weight,report))
feasible=[x for x in candidates if x[2]['false_positive_rate']<=.03 and x[2]['recall']>=.90]
model,weight,chosen=max(feasible or candidates,key=lambda x:balanced(x[2]))
out.mkdir(parents=True)
for file in ('classical.joblib','charcnn.pt','cnn-metadata.json'):shutil.copy2(Path('artifacts/release-v4')/file,out/file)
joblib.dump(model,out/'fusion.joblib')
policy={'lower':0.,'upper':1.,'fusion':'meta','cnn_weight':1.,'fusion_sha256':digest(out/'fusion.joblib'),
        'classical_sha256':digest(out/'classical.joblib'),'cnn_version':json.loads((out/'cnn-metadata.json').read_text())['version'],
        'cascade_code_sha256':digest('ml/phishx/cascade.py'),'explanation_code_sha256':digest('ml/phishx/component_shapley.py'),'probability_calibrated':False}
policy['version']='cascade-release-v5-'+hashlib.sha256(json.dumps(policy,sort_keys=True).encode()).hexdigest()[:12]
(out/'cascade-policy.json').write_text(json.dumps(policy,indent=2)+'\n')
report={'frozen_at':datetime.now(timezone.utc).isoformat(),'policy':policy,'quality_gates':gates,'cohort_manifests':seals,
        'fusion_training':{'source_sha256':digest('data/processed/release-v4/test.csv'),'fit_rows':len(fit),'review_rows':len(review),'group_overlap':0,
                           'fit_policy':'70/30 SHA256 connected-group split of unused internal calibration partition; frozen encoder/forest weights. Two shared bounded-logit score features, LogisticRegression C1, official-navigation weights1/3/10/20; select on separate calibration review FPR<=.03 recall>=.90 when feasible, then balanced accuracy. No final-set tuning.',
                           'selected_official_weight':weight,'candidates':[{'weight':w,'review':r} for _,w,r in candidates],
                           'coefficients':model.coef_.tolist(),'intercept':model.intercept_.tolist()},'cohorts':{}}
(out/'pre-evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
from phishx.cascade import CascadePredictor
candidate=CascadePredictor(out,out/'classical.joblib');old=load_bundle('artifacts/revised-run06/classical.joblib')
for name,path in cohorts.items():
    assert digest(path/'holdout.csv')==seals[name]['holdout_sha256']
    rows=load_rows(path/'holdout.csv');urls=[r['url'] for r in rows];y=[int(r['label']) for r in rows]
    p,rf,routed,analysis=candidate.predict(urls)
    baseline=old['model'].predict_proba([[a['features'][k] for k in old['feature_names']] for a in analysis])[:,1]
    report['cohorts'][name]={'rows':len(rows),'groups':len({r['group'] for r in rows}),'classical':probability_report(y,baseline),'cascade':probability_report(y,p)}
u=report['cohorts']['fresh_uci'];e=report['cohorts']['fresh_external'];g=gates
checks={'uci_recall':u['cascade']['recall']>=g['uci_min_recall'],'uci_fpr':u['cascade']['false_positive_rate']<=g['uci_max_false_positive_rate'],
        'external_recall':e['cascade']['recall']>=g['external_min_recall'],'external_fpr':e['cascade']['false_positive_rate']<=g['external_max_false_positive_rate'],
        'recall_noninferiority':all(r['cascade']['recall']>=r['classical']['recall']-.02 for r in report['cohorts'].values()),
        'fpr_did_not_worsen':all(r['cascade']['false_positive_rate']<=r['classical']['false_positive_rate'] for r in report['cohorts'].values())}
report['quality_checks']=checks;report['all_quality_gates_passed']=all(checks.values())
report['limitations']='Local academic-demo gates, not universal phishing accuracy. Historical source labels, convenience publisher cohort, no population calibration; signed component Shapley explains this model only.'
(out/'release-evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'version':policy['version'],'selected_weight':weight,'cohorts':{name:{m:{k:r[m][k] for k in ('accuracy','recall','false_positive_rate','confusion_matrix')} for m in ('classical','cascade')} for name,r in report['cohorts'].items()},'checks':checks,'passed':report['all_quality_gates_passed']},indent=2))
