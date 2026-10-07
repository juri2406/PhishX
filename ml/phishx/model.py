"""Classical baseline with validation-only selection and frozen test reporting."""
import csv
import json
import hashlib
from pathlib import Path
from time import perf_counter
from importlib.resources import files
from .features import analyze_url, FEATURE_NAMES


def load_rows(path):
    with Path(path).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def matrix(rows):
    return [[analyze_url(r['url'])['features'][key] for key in FEATURE_NAMES] for r in rows]


def resource_hashes():
    return {name:hashlib.sha256(files('phishx').joinpath('resources',name).read_bytes()).hexdigest()
            for name in ('brands.json','confusables.txt')}


def extractor_hashes():
    return {name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('features.py','urls.py','skeleton.py')}


def load_bundle(artifact):
    import joblib
    bundle = joblib.load(artifact)  # Trusted local files only.
    if bundle.get('extractor_hashes') != extractor_hashes():
        raise ValueError('Feature extractor changed. Retrain the artifact before inference.')
    expected_names = FEATURE_NAMES
    if bundle.get('feature_profile') == 'extended-v1':
        from .extended_features import EXTENDED_FEATURE_NAMES, extended_hashes
        expected_names = EXTENDED_FEATURE_NAMES
        if bundle.get('extended_extractor_hashes') != extended_hashes():
            raise ValueError('Extended feature extractor changed. Retrain the artifact.')
    elif bundle.get('feature_profile', 'lexical-v1') != 'lexical-v1':
        raise ValueError('Unknown feature profile.')
    if bundle['feature_names'] != list(expected_names):
        raise ValueError('Model feature schema mismatch.')
    if bundle['resource_hashes'] != resource_hashes():
        raise ValueError('Model resource version mismatch. Retrain the model.')
    if list(bundle['model'].classes_) != [0,1]:
        raise ValueError('Expected binary labels 0=benign and 1=phishing.')
    return bundle


def probability_report(y, prob):
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    from sklearn.metrics import confusion_matrix, roc_auc_score, brier_score_loss, log_loss
    import numpy as np
    y = np.asarray(y); prob = np.asarray(prob)
    pred = prob >= .5
    tn,fp,fn,tp = confusion_matrix(y,pred,labels=[0,1]).ravel()
    bins=[]
    for index in range(10):
        mask=(prob >= index/10) & (prob < (index+1)/10 if index<9 else prob <= 1)
        if mask.any():
            bins.append(dict(lower=index/10, upper=(index+1)/10, count=int(mask.sum()),
                             mean_probability=float(prob[mask].mean()), phishing_fraction=float(y[mask].mean())))
    return dict(rows=len(y), phishing_rows=int(sum(y)), benign_rows=int(len(y)-sum(y)),
                accuracy=float(accuracy_score(y,pred)), precision=float(precision_score(y,pred,zero_division=0)),
                recall=float(recall_score(y,pred,zero_division=0)), f1=float(f1_score(y,pred,zero_division=0)),
                false_positive_rate=float(fp/(fp+tn)) if fp+tn else None,
                roc_auc=float(roc_auc_score(y,prob)) if len(set(y))==2 else None,
                brier_score=float(brier_score_loss(y,prob)),log_loss=float(log_loss(y,prob,labels=[0,1])),
                confusion_matrix=[[int(tn),int(fp)],[int(fn),int(tp)]], probability_bins=bins)


def train(split_dir, output_dir):
    import joblib
    import sklearn
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.dummy import DummyClassifier
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.metrics import f1_score
    split_dir = Path(split_dir); out = Path(output_dir)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Choose an empty model output directory.')
    manifest = json.loads((split_dir/'manifest.json').read_text())
    rows = {name:load_rows(split_dir/f'{name}.csv') for name in ('train','validation','test')}
    for name in rows:
        digest=hashlib.sha256((split_dir/f'{name}.csv').read_bytes()).hexdigest()
        if manifest.get('split_sha256',{}).get(name,digest) != digest:
            raise ValueError('Prepared split checksum mismatch')
    for field in ('group_domain','actual_domain','domain_skeleton','canonical'):
        if all(field in r for rs in rows.values() for r in rs):
            groups={name:{r[field] for r in rs} for name,rs in rows.items()}
            if any(groups[a]&groups[b] for a,b in [('train','test'),('train','validation'),('validation','test')]):
                raise ValueError(f'{field} leakage across splits.')
    xs={name:np.asarray(matrix(rs)) for name,rs in rows.items()}
    ys={name:np.asarray([int(r['label']) for r in rs]) for name,rs in rows.items()}
    if any(set(y) != {0,1} for y in ys.values()):
        raise ValueError('Each split requires both labels.')
    candidates=[]
    for depth in (8,16,None):
        model=RandomForestClassifier(n_estimators=150,max_depth=depth,min_samples_leaf=2,
                                     class_weight='balanced',random_state=42,n_jobs=-1)
        model.fit(xs['train'],ys['train'])
        score=f1_score(ys['validation'],model.predict(xs['validation']),zero_division=0)
        candidates.append((float(score),model))
    score,model=max(candidates,key=lambda pair:pair[0])
    def evaluate(estimator, features=xs['test']):
        start=perf_counter()
        prob=estimator.predict_proba(features)[:,list(estimator.classes_).index(1)]
        elapsed=perf_counter()-start
        result=probability_report(ys['test'],prob)
        result['batch_model_ms_per_url']=elapsed*1000/len(prob)
        return result
    baseline=DummyClassifier(strategy='prior').fit(xs['train'],ys['train'])
    https_index=list(FEATURE_NAMES).index('https_explicit')
    https_model=DecisionTreeClassifier(max_depth=1,random_state=42).fit(xs['train'][:,[https_index]],ys['train'])
    bias={name:{str(label):dict(rows=int(sum(ys[name]==label)),
            https_fraction=float(xs[name][ys[name]==label,https_index].mean()),
            median_url_length=float(np.median(xs[name][ys[name]==label,0])))
            for label in (0,1)} for name in rows}
    report=dict(model='random_forest',sklearn_version=sklearn.__version__,selected_max_depth=model.max_depth,
                validation_f1=score, validation_candidates=[dict(max_depth=m.max_depth,f1=s) for s,m in candidates],
                validation=probability_report(ys['validation'],model.predict_proba(xs['validation'])[:,1]),
                test=evaluate(model),baseline=evaluate(baseline),
                https_only_diagnostic=evaluate(https_model,xs['test'][:,[https_index]]),
                source_bias_indicators=bias, rows={k:len(v) for k,v in rows.items()},threshold=.5,
                probability_calibrated=False, calibration_check='Brier, log loss and reliability bins only; no calibrator fitted.',
                note='Second exploratory model after formatting diagnosis. Historical source labels. Test is domain/skeleton separated, not temporal. Latency excludes feature extraction.',
                dataset_manifest=manifest, feature_names=list(FEATURE_NAMES),
                feature_importance={name:float(value) for name,value in zip(FEATURE_NAMES,model.feature_importances_)})
    version='rf-v2-'+manifest['input_sha256'][:12]+'-seed'+str(manifest['seed'])
    report['model_version']=version
    out.mkdir(parents=True,exist_ok=True)
    joblib.dump(dict(model=model,feature_names=list(FEATURE_NAMES),resource_hashes=resource_hashes(),
                     version=version,extractor_hashes=extractor_hashes(),probability_calibrated=False,sklearn_version=sklearn.__version__,
                     split_sha256=manifest.get('split_sha256',{})),out/'classical.joblib')
    report['artifact_sha256']=hashlib.sha256((out/'classical.joblib').read_bytes()).hexdigest()
    (out/'evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
    # Error details stay local with ignored artifacts, not in the repository.
    probabilities=model.predict_proba(xs['test'])[:,1]
    errors=[dict(url=r['url'],label=int(r['label']),phishing_probability=float(p))
            for r,p in zip(rows['test'],probabilities) if (p>=.5)!=bool(int(r['label']))]
    (out/'errors.json').write_text(json.dumps(errors,indent=2)+'\n')
    return report


def predict(url, artifact):
    bundle=load_bundle(artifact)
    analyze = analyze_url
    if bundle.get('feature_profile') == 'extended-v1':
        from .extended_features import analyze_extended
        analyze = analyze_extended
    analysis=analyze(url); model=bundle['model']
    probability=float(model.predict_proba([[analysis['features'][key] for key in bundle['feature_names']]])[0,1])
    score=round(100*probability)
    return dict(**analysis,phishing_probability=probability,risk_score=score,
                risk_level='Low' if score<=30 else 'Medium' if score<=60 else 'High' if score<=80 else 'Critical',
                model_used='classical',cascade_status='not_implemented',model_version=bundle['version'],
                probability_calibrated=bundle.get('probability_calibrated',False))
