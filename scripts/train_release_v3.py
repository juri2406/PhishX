"""Final data revision: all inspected sets are development; fresh tests open last."""
import argparse,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
import joblib,numpy as np,sklearn,torch
from sklearn.ensemble import RandomForestClassifier
from torch.utils.data import TensorDataset,DataLoader
from phishx.charcnn import CharacterCNN,encode,vocabulary,code_hash,CNNPredictor
from phishx.model import load_rows,probability_report,extractor_hashes,resource_hashes,load_bundle
from phishx.extended_features import analyze_extended,EXTENDED_FEATURE_NAMES,extended_hashes

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def balanced(r):return (r['recall']+1-r['false_positive_rate'])/2

def train():
    out=Path('artifacts/release-v3');splits=Path('data/processed/release-v3')
    if out.exists():raise ValueError('Use a new release revision')
    # These gates are frozen before test loading; no post-test tuning.
    gates=json.loads(Path('work/completion/release-plan.json').read_text())['quality_gates']
    holdouts={'fresh_uci':Path('data/processed/completion-uci03'),'fresh_external':Path('data/processed/completion-external03')}
    seals={name:json.loads((p/'manifest.json').read_text()) for name,p in holdouts.items()}
    for name,p in holdouts.items():assert digest(p/'holdout.csv')==seals[name]['holdout_sha256']
    torch.set_num_threads(4);torch.manual_seed(42);np.random.seed(42);torch.use_deterministic_algorithms(True)
    manifest=json.loads((splits/'manifest.json').read_text())
    rows={n:load_rows(splits/f'{n}.csv') for n in ('train','validation')}
    for n in rows:assert digest(splits/f'{n}.csv')==manifest['split_sha256'][n]
    ys={n:np.array([int(r['label']) for r in rs]) for n,rs in rows.items()}
    features={n:[analyze_extended(r['url'])['features'] for r in rs] for n,rs in rows.items()}
    xs={n:np.array([[f[k] for k in EXTENDED_FEATURE_NAMES] for f in fs]) for n,fs in features.items()}
    weights=np.array([10. if r['source'].startswith('official-navigation:') else 1. for r in rows['train']])
    forests=[]
    for depth in (8,16):
        for leaf in (2,5):
            model=RandomForestClassifier(n_estimators=150,max_depth=depth,min_samples_leaf=leaf,class_weight='balanced',random_state=42,n_jobs=4).fit(xs['train'],ys['train'],sample_weight=weights)
            r=probability_report(ys['validation'],model.predict_proba(xs['validation'])[:,1]);forests.append((balanced(r),model,r))
    _,forest,rf_selection=max(forests,key=lambda r:r[0]);out.mkdir(parents=True)
    bundle={'model':forest,'feature_names':list(EXTENDED_FEATURE_NAMES),'feature_profile':'extended-v1','extended_extractor_hashes':extended_hashes(),
            'extractor_hashes':extractor_hashes(),'resource_hashes':resource_hashes(),'version':'rf-release-v3-'+manifest['input_sha256'][:12],
            'sklearn_version':sklearn.__version__,'probability_calibrated':False,'split_sha256':manifest['split_sha256']}
    joblib.dump(bundle,out/'classical.joblib')
    chars=vocabulary([r['url'] for r in rows['train']]);tokens={n:encode([r['url'] for r in rs],chars) for n,rs in rows.items()}
    cnn=CharacterCNN(len(chars)+2);optimizer=torch.optim.AdamW(cnn.parameters(),lr=.001,weight_decay=.0001);loss_fn=torch.nn.BCEWithLogitsLoss(reduction='none')
    loader=DataLoader(TensorDataset(tokens['train'],torch.tensor(ys['train'],dtype=torch.float32),torch.tensor(weights,dtype=torch.float32)),batch_size=128,shuffle=True,generator=torch.Generator().manual_seed(42))
    def predict_tokens(t):
        cnn.eval()
        with torch.inference_mode():return np.concatenate([torch.sigmoid(cnn(t[i:i+128])).numpy() for i in range(0,len(t),128)])
    best=-1.;history=[]
    for epoch in range(8):
        cnn.train();total=0.
        for batch,y,w in loader:
            optimizer.zero_grad();loss=(loss_fn(cnn(batch),y)*w).mean();loss.backward();optimizer.step();total+=float(loss.detach())*len(y)
        r=probability_report(ys['validation'],predict_tokens(tokens['validation']));history.append({'epoch':epoch+1,'loss':total/len(rows['train']),'selection':r})
        print(json.dumps({'epoch':epoch+1,'balanced_accuracy':balanced(r),'fpr':r['false_positive_rate'],'recall':r['recall']}),flush=True)
        if balanced(r)>best:best=balanced(r);best_epoch=epoch+1;torch.save(cnn.state_dict(),out/'charcnn.pt')
    cnn.load_state_dict(torch.load(out/'charcnn.pt',weights_only=True));cnn.eval();nn_prob=predict_tokens(tokens['validation']);rf_prob=forest.predict_proba(xs['validation'])[:,1]
    candidates=[]
    for lower,upper,fusion,weight in [(.5,.9,'minimum',1.),(.3,.9,'blend',.5),(.2,.9,'blend',.5),(.1,.9,'blend',.5),(.1,.9,'blend',1.)]:
        routed=(rf_prob>=lower)&(rf_prob<=upper);p=rf_prob.copy();p[routed]=np.minimum(rf_prob[routed],nn_prob[routed]) if fusion=='minimum' else (1-weight)*rf_prob[routed]+weight*nn_prob[routed]
        r=probability_report(ys['validation'],p);candidates.append({'lower':lower,'upper':upper,'fusion':fusion,'cnn_weight':weight,'selection':r})
    feasible=[c for c in candidates if c['selection']['false_positive_rate']<=.05 and c['selection']['recall']>=.88]
    chosen=max(feasible or candidates,key=lambda c:balanced(c['selection']))
    meta={'architecture':'charcnn-v1','version':'charcnn-v3-'+digest(out/'charcnn.pt')[:12],'characters':chars,'code_sha256':code_hash(),'weights_sha256':digest(out/'charcnn.pt'),
          'extractor_hashes':extractor_hashes(),'resource_hashes':resource_hashes(),'torch_version':str(torch.__version__),'best_epoch':best_epoch,'max_length':512,'probability_calibrated':False}
    (out/'cnn-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    policy={k:chosen[k] for k in ('lower','upper','fusion','cnn_weight')};policy.update(classical_sha256=digest(out/'classical.joblib'),cnn_version=meta['version'],
           cascade_code_sha256=digest('ml/phishx/cascade.py'),explanation_code_sha256=digest('ml/phishx/component_shapley.py'),probability_calibrated=False)
    policy['version']='cascade-release-v3-'+hashlib.sha256(json.dumps(policy,sort_keys=True).encode()).hexdigest()[:12]
    (out/'cascade-policy.json').write_text(json.dumps(policy,indent=2)+'\n')
    report={'frozen_at':datetime.now(timezone.utc).isoformat(),'policy':policy,'quality_gates':gates,'data_manifest':manifest,'cohort_manifests':seals,
            'training_policy':'All earlier inspected holdouts now development. Connected-group splits; fixed 8 CNN epochs, select by validation balanced accuracy. Official navigation rows weight 10. RF grid depth8/16 leaf2/5. Cascade uses validation only; prefer selection FPR<=.05 and recall>=.88, then balanced accuracy. Threshold0.5 fixed.',
            'rf_selection':rf_selection,'cnn_epochs':history,'cascade_candidates':candidates,'cohorts':{}}
    # Strip any raw rejected input records from distributable aggregate evidence.
    report['data_manifest'].pop('rejected',None)
    (out/'pre-evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
    from phishx.cascade import CascadePredictor
    candidate=CascadePredictor(out,out/'classical.joblib');old=load_bundle('artifacts/revised-run06/classical.joblib')
    for name,p in holdouts.items():
        assert digest(p/'holdout.csv')==seals[name]['holdout_sha256']
        rs=load_rows(p/'holdout.csv');urls=[r['url'] for r in rs];y=[int(r['label']) for r in rs]
        final,new_rf,routed,analyses=candidate.predict(urls)
        old_rf=old['model'].predict_proba([[a['features'][k] for k in old['feature_names']] for a in analyses])[:,1]
        report['cohorts'][name]={'rows':len(rs),'groups':len({r['group'] for r in rs}),'classical':probability_report(y,old_rf),
                               'new_forest':probability_report(y,new_rf),'cascade':probability_report(y,final),'routed_fraction':float(routed.mean())}
    u=report['cohorts']['fresh_uci'];e=report['cohorts']['fresh_external'];g=gates
    checks={'uci_recall':u['cascade']['recall']>=g['uci_min_recall'],'uci_fpr':u['cascade']['false_positive_rate']<=g['uci_max_false_positive_rate'],
            'external_recall':e['cascade']['recall']>=g['external_min_recall'],'external_fpr':e['cascade']['false_positive_rate']<=g['external_max_false_positive_rate'],
            'recall_noninferiority':all(r['cascade']['recall']>=r['classical']['recall']-.02 for r in report['cohorts'].values()),
            'fpr_did_not_worsen':all(r['cascade']['false_positive_rate']<=r['classical']['false_positive_rate'] for r in report['cohorts'].values())}
    report['quality_checks']=checks;report['all_quality_gates_passed']=all(checks.values());report['scope']='Local academic demo, not population accuracy or production safety certification.'
    (out/'release-evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'version':policy['version'],'policy':policy,'cohorts':{n:{model:{k:r[model][k] for k in ('accuracy','recall','false_positive_rate')} for model in ('classical','new_forest','cascade')} for n,r in report['cohorts'].items()},'checks':checks,'passed':report['all_quality_gates_passed']},indent=2),flush=True)
if __name__=='__main__':train()
