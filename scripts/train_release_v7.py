"""Learn frozen popularity context without whitelists; open fresh tests last."""
import csv,io,zipfile,hashlib,json,shutil
from pathlib import Path
from datetime import datetime,timezone
import joblib,numpy as np,torch
from sklearn.ensemble import HistGradientBoostingClassifier
from threadpoolctl import threadpool_limits
from phishx.model import load_rows,load_bundle,probability_report
from phishx.charcnn import CNNPredictor
from phishx.urls import normalize_url
from phishx.dataset import domain_skeleton
from phishx.extended_features import analyze_extended
from phishx.ranked_context import context_matrix,CONTEXT_NAMES

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def balanced(r):return (r['recall']+1-r['false_positive_rate'])/2
out=Path('artifacts/release-v7')
if out.exists():raise ValueError('Use a new revision')
cohorts={'fresh_uci':Path('data/processed/completion-uci07'),'fresh_external':Path('data/processed/completion-external07')}
seals={n:json.loads((p/'manifest.json').read_text()) for n,p in cohorts.items()}
for n,p in cohorts.items():assert digest(p/'holdout.csv')==seals[n]['holdout_sha256']
gates=json.loads(Path('docs/evidence/completion/release-v7-plan.json').read_text())['gates']
archive=Path('data/raw/tranco-20261021.csv.zip');ranks={}
with zipfile.ZipFile(archive) as z:
    with z.open('top-1m.csv') as f:
        for rank,domain in csv.reader(io.TextIOWrapper(f,encoding='utf-8')):
            rank=int(rank)
            if 1<=rank<=1000000:ranks.setdefault(domain.lower().rstrip('.'),rank)
assert len(ranks)>=900000
# The test ranking context is unlabelled external data, never a benign override.
pool=load_rows('data/processed/release-v7/development.csv')
blocked=set()
for split in ('train','validation'):
    blocked.update(r['domain_skeleton'] for r in load_rows(f'data/processed/release-v4/{split}.csv'))
unique={}
for r in pool:
    parsed=normalize_url(r['url']);group=domain_skeleton(parsed.registrable_domain)
    unique[(parsed.canonical,int(r['label']))]={'url':parsed.canonical,'label':int(r['label']),'group':group,'source':r['source']}
labels={}
for canonical,label in unique:labels.setdefault(canonical,set()).add(label)
rows=[r for (canonical,label),r in unique.items() if len(labels[canonical])==1]
review_groups={r['group'] for r in rows if r['group'] not in blocked and int(hashlib.sha256(('ranked-v7:'+r['group']).encode()).hexdigest()[:8],16)%10>=7}
fit=[r for r in rows if r['group'] not in review_groups];review=[r for r in rows if r['group'] in review_groups]
assert not {r['group'] for r in fit}&review_groups
assert not blocked&review_groups
bundle=load_bundle('artifacts/release-v4/classical.joblib');cnn=CNNPredictor('artifacts/release-v4');torch.set_num_threads(4)
def transform(rs):
    urls=[r['url'] for r in rs];analysis=[analyze_extended(u) for u in urls]
    rf=bundle['model'].predict_proba([[a['features'][name] for name in bundle['feature_names']] for a in analysis])[:,1]
    return context_matrix(rf,cnn.probabilities(urls),analysis,ranks)
xfit,xreview=transform(fit),transform(review);yfit=[r['label'] for r in fit];yreview=[r['label'] for r in review]
candidates=[]
with threadpool_limits(limits=4):
    for dropout in (0.,.25,.5):
        augmented=xfit.copy()
        masked=np.random.default_rng(20261021).random(len(fit))<dropout
        augmented[masked,2]=0.;augmented[masked,3]=np.log10(1000001)
        for leaves in (15,31):
            for weight in (1.,3.,10.):
                model=HistGradientBoostingClassifier(max_iter=150,max_leaf_nodes=leaves,learning_rate=.1,l2_regularization=1.,early_stopping=False,random_state=42).fit(augmented,yfit,sample_weight=[weight if r['source'].startswith('official-navigation:') else 1. for r in fit])
                r=probability_report(yreview,model.predict_proba(xreview)[:,1]);candidates.append((model,leaves,weight,dropout,r))
feasible=[c for c in candidates if c[4]['false_positive_rate']<=.02 and c[4]['recall']>=.95]
model,leaves,weight,dropout,chosen=max(feasible or candidates,key=lambda c:balanced(c[4]))
out.mkdir(parents=True)
for file in ('classical.joblib','charcnn.pt','cnn-metadata.json'):shutil.copy2(Path('artifacts/release-v4')/file,out/file)
joblib.dump(model,out/'fusion.joblib');joblib.dump(ranks,out/'rank-context.joblib',compress=3)
policy={'lower':0.,'upper':1.,'fusion':'ranked','cnn_weight':1.,'fusion_sha256':digest(out/'fusion.joblib'),
        'rank_context_sha256':digest(out/'rank-context.joblib'),'context_code_sha256':digest('ml/phishx/ranked_context.py'),'context_names':list(CONTEXT_NAMES),
        'classical_sha256':digest(out/'classical.joblib'),'cnn_version':json.loads((out/'cnn-metadata.json').read_text())['version'],
        'cascade_code_sha256':digest('ml/phishx/cascade.py'),'explanation_code_sha256':digest('ml/phishx/component_shapley.py'),'probability_calibrated':False}
policy['version']='cascade-release-v7-'+hashlib.sha256(json.dumps(policy,sort_keys=True).encode()).hexdigest()[:12]
(out/'cascade-policy.json').write_text(json.dumps(policy,indent=2)+'\n')
report={'frozen_at':datetime.now(timezone.utc).isoformat(),'policy':policy,'quality_gates':gates,'cohort_manifests':seals,
        'ranking_source':{'provider':'Tranco','list_id':Path('work/completion/tranco-list-id.txt').read_text().strip(),'snapshot_sha256':digest(archive),'rows':len(ranks),
                          'source':'https://tranco-list.eu/','purpose':'Unlabelled frozen popularity context as learned numeric features. Presence/rank never directly sets a verdict. Both malicious and benign URLs may use ranked domains.',
                          'time_limitation':'Ranking snapshot is later than historical URL labels; this is not forward-temporal validation.'},
        'fusion_training':{'fit_rows':len(fit),'review_rows':len(review),'group_overlap':0,'review_encoder_training_group_overlap':0,
                           'policy':'Frozen v4 encoder and forest. Fit on expanded official navigation, internal calibration and all earlier inspected completion cohorts; SHA256 group split, review groups exclude upstream encoder train/selection. HistGradientBoosting 150 rounds, leaves15/31, official weights1/3/10, seeded training-only rank masking0/.25/.5; validation-only balanced accuracy with FPR<=.02/recall>=.95 preference. Review uses unmodified actual context. No test-driven changes.',
                           'selected_leaves':leaves,'selected_official_weight':weight,'selected_rank_dropout':dropout,'candidates':[{'leaves':l,'weight':w,'dropout':d,'review':r} for _,l,w,d,r in candidates]},'cohorts':{}}
(out/'pre-evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
from phishx.cascade import CascadePredictor
candidate=CascadePredictor(out,out/'classical.joblib');old=load_bundle('artifacts/revised-run06/classical.joblib')
with threadpool_limits(limits=4):
    for name,path in cohorts.items():
        assert digest(path/'holdout.csv')==seals[name]['holdout_sha256']
        rs=load_rows(path/'holdout.csv');urls=[r['url'] for r in rs];y=[int(r['label']) for r in rs]
        p,rf,routed,analysis=candidate.predict(urls)
        baseline=old['model'].predict_proba([[a['features'][k] for k in old['feature_names']] for a in analysis])[:,1]
        report['cohorts'][name]={'rows':len(rs),'groups':len({r['group'] for r in rs}),'classical':probability_report(y,baseline),'cascade':probability_report(y,p)}
u=report['cohorts']['fresh_uci'];e=report['cohorts']['fresh_external'];g=gates
checks={'uci_recall':u['cascade']['recall']>=g['uci_min_recall'],'uci_fpr':u['cascade']['false_positive_rate']<=g['uci_max_false_positive_rate'],
        'external_recall':e['cascade']['recall']>=g['external_min_recall'],'external_fpr':e['cascade']['false_positive_rate']<=g['external_max_false_positive_rate'],
        'recall_noninferiority':all(r['cascade']['recall']>=r['classical']['recall']-.02 for r in report['cohorts'].values()),
        'fpr_did_not_worsen':all(r['cascade']['false_positive_rate']<=r['classical']['false_positive_rate'] for r in report['cohorts'].values())}
report['quality_checks']=checks;report['all_quality_gates_passed']=all(checks.values())
report['limitations']='Academic local-demo validation only. Repeated research revisions and convenience samples are disclosed; no population accuracy, calibrated web-risk probability or production guarantee.'
(out/'release-evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'version':policy['version'],'selected':{'leaves':leaves,'weight':weight},'cohorts':{n:{m:{k:r[m][k] for k in ('accuracy','recall','false_positive_rate','confusion_matrix')} for m in ('classical','cascade')} for n,r in report['cohorts'].items()},'checks':checks,'passed':report['all_quality_gates_passed']},indent=2))
