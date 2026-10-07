"""Summarize a frozen revised model without tuning against its final results."""
import argparse
import json
import hashlib
from pathlib import Path
import numpy as np
import idna
from phishx.model import load_bundle,load_rows,matrix,probability_report
from phishx.robustness import variant,FAMILIES
from phishx.urls import InvalidURL


def summarize(splits,artifact,output):
    splits,artifact,output=Path(splits),Path(artifact),Path(output)
    if output.exists(): raise ValueError('Choose a new report output')
    bundle=load_bundle(artifact)
    def candidate_matrix(rs):
        if bundle.get('feature_profile')!='extended-v1': return matrix(rs)
        from phishx.extended_features import analyze_extended
        features=[analyze_extended(r['url'])['features'] for r in rs]
        return [[f[name] for name in bundle['feature_names']] for f in features]
    model=bundle['model']
    report=json.loads(artifact.with_name('evaluation.json').read_text())
    if hashlib.sha256(artifact.read_bytes()).hexdigest()!=report['artifact_sha256']:
        raise ValueError('Artifact differs from frozen evaluation')
    if hashlib.sha256((splits/'final.csv').read_bytes()).hexdigest()!=bundle['split_sha256']['final']:
        raise ValueError('Final partition differs from frozen artifact')
    rows=load_rows(splits/'final.csv'); x=np.asarray(matrix(rows));y=[int(r['label']) for r in rows]
    old=load_bundle('artifacts/uci-run03/classical.joblib')['model']
    report['legacy_on_same_final']=probability_report(y,old.predict_proba(x)[:,1])
    report['stress']={}
    for family in FAMILIES:
        original=[];changed=[];skipped=0
        for row in rows:
            if row['label']!='1':continue
            try:
                url=variant(row['url'],family)
                if not url:
                    skipped+=1;continue
                candidate_matrix([{'url':url}])
            except (InvalidURL,idna.IDNAError):
                skipped+=1;continue
            original.append(row);changed.append({'url':url})
            if len(changed)==200:break
        orig_prob=model.predict_proba(candidate_matrix(original))[:,1]
        mod_prob=model.predict_proba(candidate_matrix(changed))[:,1]
        report['stress'][family]={'rows':len(changed),'skipped_before_cap':skipped,
            'paired_original_recall':float((orig_prob>=.5).mean()),'variant_recall':float((mod_prob>=.5).mean()),
            'lost_detections':int(((orig_prob>=.5)&(mod_prob<.5)).sum())}
    urls=['https://paypal.com/login','https://github.com/juri2406/PhishX','https://github.com/',
          'https://www.w3.org/TR/2023/REC-WCAG22-20231005/','https://pаypal.com/login']
    controls=matrix([{'url':url} for url in urls])
    new_prob=model.predict_proba(candidate_matrix([{'url':url} for url in urls]))[:,1];old_prob=old.predict_proba(controls)[:,1]
    report['previously_observed_diagnostics']=[{'url':url,'old_risk_score':round(float(a)*100),
        'new_risk_score':round(float(b)*100),'new_predicted_phishing':bool(b>=.5)} for url,a,b in zip(urls,old_prob,new_prob)]
    report['final_domains_by_label']={label:len({r['actual_domain'] for r in rows if r['label']==label}) for label in ('0','1')}
    report['stress_caveat']='Offline synthetic strings, not live verified attack pages. No generated variants trained; naturally occurring obfuscation can occur in the real sources.'
    # No raw dataset URLs in the distributable report or its embedded cleaning log.
    report['manifest']['cleaning'].pop('rejected',None)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:report[key] for key in ('model_version','final','legacy_on_same_final','stress','previously_observed_diagnostics','final_domains_by_label')},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('splits');p.add_argument('artifact');p.add_argument('output')
    a=p.parse_args();summarize(a.splits,a.artifact,a.output)
