"""Select a forest, review calibration separately, freeze, then evaluate once."""
import argparse
import hashlib
import json
from pathlib import Path
import joblib
import numpy as np
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from phishx.model import load_rows,matrix,probability_report,extractor_hashes,resource_hashes
from phishx import FEATURE_NAMES
from phishx.extended_features import EXTENDED_FEATURE_NAMES, analyze_extended, extended_hashes


def train_revised(splits,output):
    splits,output=Path(splits),Path(output)
    if output.exists(): raise ValueError('Choose a new output directory')
    manifest=json.loads((splits/'manifest.json').read_text())
    names=EXTENDED_FEATURE_NAMES if manifest.get('round',4)>=6 else FEATURE_NAMES
    def rows_matrix(rs):
        if len(names)==18: return matrix(rs)
        features=[analyze_extended(r['url'])['features'] for r in rs]
        return [[f[name] for name in names] for f in features]
    # Final rows are deliberately not loaded until the artifact has been saved.
    rows={name:load_rows(splits/f'{name}.csv') for name in ('train','selection','calibration_fit','calibration_review')}
    for name in rows:
        assert hashlib.sha256((splits/f'{name}.csv').read_bytes()).hexdigest()==manifest['split_sha256'][name]
    xs={name:np.asarray(rows_matrix(rs)) for name,rs in rows.items()}
    ys={name:np.asarray([int(r['label']) for r in rs]) for name,rs in rows.items()}
    candidates=[]
    for depth in (8,16,None):
        for leaf in (2,5):
            model=RandomForestClassifier(n_estimators=150,max_depth=depth,min_samples_leaf=leaf,
                class_weight='balanced',random_state=42,n_jobs=-1).fit(xs['train'],ys['train'],
                    sample_weight=np.array([3.0 if manifest.get('round',4) >= 5 and r['source'].startswith('official-navigation:') else 1.0 for r in rows['train']]))
            report=probability_report(ys['selection'],model.predict_proba(xs['selection'])[:,1])
            # Fixed validation-only tradeoff: retain F1 while penalizing false alarms.
            criterion=(report['recall']+1-report['false_positive_rate'])/2 if manifest.get('round',4) >= 5 else report['f1']-.25*report['false_positive_rate']
            candidates.append((criterion,model,report))
    _,model,selection=max(candidates,key=lambda item:item[0])
    review={'raw':probability_report(ys['calibration_review'],model.predict_proba(xs['calibration_review'])[:,1])}
    for method in ('sigmoid','isotonic'):
        calibrated=CalibratedClassifierCV(FrozenEstimator(model),method=method)
        calibrated.fit(xs['calibration_fit'],ys['calibration_fit'])
        review[method]=probability_report(ys['calibration_review'],calibrated.predict_proba(xs['calibration_review'])[:,1])
    version='rf-v'+str(manifest.get('round',4))+'-'+manifest['cleaning']['input_sha256'][:12]+'-20261007'
    output.mkdir(parents=True)
    bundle=dict(model=model,feature_names=list(names),resource_hashes=resource_hashes(),extractor_hashes=extractor_hashes(),
                version=version,probability_calibrated=False,sklearn_version=sklearn.__version__,
                split_sha256=manifest['split_sha256'])
    if len(names)>18:
        bundle.update(feature_profile='extended-v1',extended_extractor_hashes=extended_hashes())
    joblib.dump(bundle,output/'classical.joblib')
    frozen_hash=hashlib.sha256((output/'classical.joblib').read_bytes()).hexdigest()
    # Keep served raw probabilities: review sample is nonrepresentative and few
    # benign domain groups. Calibrators were assessed, not validated for deployment.
    report={'model_version':version,'artifact_sha256':frozen_hash,'manifest':manifest,
            'selected_depth':model.max_depth,'selected_min_leaf':model.min_samples_leaf,
            'training_policy':('Official-navigation training examples have weight 3; validation balanced accuracy chooses the forest; threshold 0.5 fixed.' if manifest.get('round',4) >= 5 else 'Unweighted examples; validation F1 minus 0.25 FPR chooses forest; threshold 0.5 fixed.'),
            'selection':selection,'candidates':[dict(depth=m.max_depth,min_leaf=m.min_samples_leaf,criterion=s,metrics=r) for s,m,r in candidates],
            'calibration_review':review,'probability_calibrated':False,
            'calibration_decision':'Retain raw random-forest probabilities and the existing probability SHAP contract. Convenience-source/class proportions and small benign domain counts do not validate population calibration. Sigmoid/isotonic are reviewed only, not served.',
            'final_policy':'Artifact saved and hashed before final CSV is opened. No post-final tuning in this run.'}
    (output/'pre-final-review.json').write_text(json.dumps(report,indent=2)+'\n')
    final_path=splits/'final.csv'
    assert hashlib.sha256(final_path.read_bytes()).hexdigest()==manifest['split_sha256']['final']
    final=load_rows(final_path); y=np.array([int(r['label']) for r in final]); prob=model.predict_proba(rows_matrix(final))[:,1]
    report['final']=probability_report(y,prob)
    report['final_by_source']={}
    for source in sorted({r['source'].split(':')[0] for r in final}):
        mask=np.array([r['source'].split(':')[0]==source for r in final])
        report['final_by_source'][source]=probability_report(y[mask],prob[mask])
    (output/'evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'final-errors.json').write_text(json.dumps([dict(url=r['url'],label=int(r['label']),probability=float(p)) for r,p in zip(final,prob) if (p>=.5)!=bool(int(r['label']))],indent=2))
    print(json.dumps({k:report[k] for k in ('model_version','artifact_sha256','selected_depth','selected_min_leaf','final','final_by_source','calibration_review')},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('splits');p.add_argument('output')
    a=p.parse_args();train_revised(a.splits,a.output)
