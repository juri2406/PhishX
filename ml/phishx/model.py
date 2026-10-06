import csv
import json
import hashlib
from pathlib import Path
from time import perf_counter
from .features import analyze_url, FEATURE_NAMES

def load_rows(path):
    with Path(path).open(encoding='utf-8', newline='') as f: return list(csv.DictReader(f))

def matrix(rows):
    return [[analyze_url(r['url'])['features'][key] for key in FEATURE_NAMES] for r in rows]

def train(split_dir, output_dir):
    import joblib
    import sklearn
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.dummy import DummyClassifier
    from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score
    split_dir=Path(split_dir); out=Path(output_dir)
    if out.exists() and any(out.iterdir()): raise ValueError('Choose an empty model output directory.')
    rows={name:load_rows(split_dir/f'{name}.csv') for name in ('train','validation','test')}
    groups={name:{r['group_domain'] for r in rs} for name,rs in rows.items()}
    if any(groups[a]&groups[b] for a,b in [('train','test'),('train','validation'),('validation','test')]):
        raise ValueError('Domain leakage across splits.')
    xs={name:matrix(rs) for name,rs in rows.items()}; ys={name:[int(r['label']) for r in rs] for name,rs in rows.items()}
    if any(set(y) != {0,1} for y in ys.values()): raise ValueError('Each split requires both labels.')
    candidates=[]
    for depth in (8,16,None):
        model=RandomForestClassifier(n_estimators=150, max_depth=depth, min_samples_leaf=2, class_weight='balanced', random_state=42,n_jobs=-1)
        model.fit(xs['train'],ys['train'])
        candidates.append((f1_score(ys['validation'],model.predict(xs['validation']),zero_division=0),model))
    score, model=max(candidates,key=lambda pair:pair[0])
    def evaluate(estimator):
        start=perf_counter(); pred=estimator.predict(xs['test']); elapsed=perf_counter()-start
        tn,fp,fn,tp=confusion_matrix(ys['test'],pred,labels=[0,1]).ravel()
        prob=estimator.predict_proba(xs['test'])[:,list(estimator.classes_).index(1)]
        return dict(precision=float(precision_score(ys['test'],pred,zero_division=0)), recall=float(recall_score(ys['test'],pred,zero_division=0)), f1=float(f1_score(ys['test'],pred,zero_division=0)), false_positive_rate=float(fp/(fp+tn)), roc_auc=float(roc_auc_score(ys['test'],prob)), confusion_matrix=[[int(tn),int(fp)],[int(fn),int(tp)]], batch_model_ms_per_url=elapsed*1000/len(pred))
    baseline=DummyClassifier(strategy='prior').fit(xs['train'],ys['train'])
    report=dict(model='random_forest', sklearn_version=sklearn.__version__, selected_max_depth=model.max_depth,
                validation_f1=float(score), test=evaluate(model), baseline=evaluate(baseline),
                rows={k:len(v) for k,v in rows.items()}, threshold=.5,
                note='Probability is uncalibrated. Latency excludes parsing and feature extraction.',
                dataset_manifest=json.loads((split_dir/'manifest.json').read_text()))
    out.mkdir(parents=True,exist_ok=True)
    hashes={name:hashlib.sha256(Path(__file__).with_name('resources').joinpath(name).read_bytes()).hexdigest() for name in ('brands.json','confusables.txt')}
    joblib.dump(dict(model=model,feature_names=list(FEATURE_NAMES),resource_hashes=hashes,version='rf-'+report['dataset_manifest']['input_sha256'][:12]+'-seed'+str(report['dataset_manifest']['seed'])),out/'classical.joblib')
    (out/'evaluation.json').write_text(json.dumps(report,indent=2)); return report

def predict(url, artifact):
    import joblib
    # Only load trusted local artifacts: joblib deserialization can execute code.
    bundle=joblib.load(artifact)
    if bundle['feature_names'] != list(FEATURE_NAMES): raise ValueError('Model feature schema mismatch.')
    for name, expected in bundle['resource_hashes'].items():
        actual=hashlib.sha256(Path(__file__).with_name('resources').joinpath(name).read_bytes()).hexdigest()
        if actual != expected: raise ValueError('Model resource version mismatch. Retrain the model.')
    analysis=analyze_url(url); model=bundle['model']
    probability=float(model.predict_proba([[analysis['features'][key] for key in FEATURE_NAMES]])[0,list(model.classes_).index(1)])
    score=round(100*probability)
    return dict(**analysis, phishing_probability=probability,risk_score=score,
                risk_level='Low' if score<=30 else 'Medium' if score<=60 else 'High' if score<=80 else 'Critical',
                model_used='classical', cascade_status='not_implemented', model_version=bundle['version'],
                probability_calibrated=False)
