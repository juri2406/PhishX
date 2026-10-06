"""Evaluate an untouched domain-disjoint source subset after freezing a model."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import idna
from phishx.urls import normalize_url, InvalidURL
from phishx.dataset import domain_skeleton
from phishx.model import load_bundle, load_rows, matrix, probability_report
from phishx.robustness import variant, FAMILIES


def evaluate(artifact, fresh_csv, original_csv, output):
    artifact, fresh_csv, original_csv, output = map(Path,(artifact,fresh_csv,original_csv,output))
    if output.exists():
        raise ValueError('Choose a new external evaluation output')
    bundle=load_bundle(artifact); model=bundle['model']
    old_domains=set()
    for row in load_rows(original_csv):
        try:
            old_domains.add(domain_skeleton(normalize_url(row['url']).registrable_domain))
        except InvalidURL:
            continue
    input_rows=load_rows(fresh_csv)
    unique={}; conflicts=set(); duplicates=0
    for row in input_rows:
        key=normalize_url(row['url']).canonical
        if key in unique:
            if unique[key]['label']!=row['label']:
                conflicts.add(key)
            else:
                duplicates+=1
        else:
            unique[key]=row
    rows=[r for key,r in unique.items() if key not in conflicts]
    fresh_domains={domain_skeleton(normalize_url(row['url']).registrable_domain) for row in rows}
    if old_domains & fresh_domains:
        raise ValueError('Fresh evaluation overlaps domains/skeletons from the previous run')
    if any(row['family']!='original' for row in rows):
        raise ValueError('External real-data metrics require original source rows')
    x=np.asarray(matrix(rows)); y=[int(row['label']) for row in rows]
    probabilities=model.predict_proba(x)[:,1]
    report=dict(model_version=bundle['version'],artifact_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),
                prior_input_sha256=hashlib.sha256(original_csv.read_bytes()).hexdigest(),
                external_input_sha256=hashlib.sha256(fresh_csv.read_bytes()).hexdigest(),
                source=json.loads(fresh_csv.with_suffix('.sources.json').read_text()),
                prior_domain_skeleton_overlap=0, domain_skeleton_groups=len(fresh_domains),
                input_rows=len(input_rows),duplicates_removed=duplicates,conflicting_urls_removed=len(conflicts),
                test=probability_report(y,probabilities), families={},
                caveat='Fresh held-out records and domain groups, but the same historical UCI source. No external-source or temporal generalization claim.')
    for family in FAMILIES:
        originals=[]; variants=[]; skipped=0
        for row in rows:
            if row['label']!='1':
                continue
            try:
                changed=variant(row['url'],family)
                if changed:
                    matrix([dict(url=changed)]) # Validate before collecting.
                    originals.append(row);variants.append(dict(url=changed))
                else:
                    skipped+=1
            except (InvalidURL,idna.IDNAError):
                skipped+=1
                continue
            if len(variants)>=200:
                break
        if not variants:
            report['families'][family]=dict(rows=0,recall=None);continue
        original_prob=model.predict_proba(matrix(originals))[:,1]
        variant_prob=model.predict_proba(matrix(variants))[:,1]
        report['families'][family]=dict(rows=len(variants),skipped_before_limit=skipped,paired_original_recall=float((original_prob>=.5).mean()),
                recall=float((variant_prob>=.5).mean()),lost_detections=int(((original_prob>=.5)&(variant_prob<.5)).sum()))
    controls=['https://paypal.com','https://paypal.com/','https://www.paypal.com','https://www.paypal.com/',
              'https://paypal.com/login','https://github.com/','https://github.com/juri2406/PhishX']
    control_prob=model.predict_proba(matrix([dict(url=url) for url in controls]))[:,1]
    report['known_domain_formatting_controls']=[dict(url=url,risk_score=round(float(p)*100),
                predicted_phishing=bool(p>=.5)) for url,p in zip(controls,control_prob)]
    report['control_caveat']='Known official-domain URL-string controls. Content/current compromise status is not fetched or independently verified. These controls are diagnostic, not a new real-data accuracy benchmark.'
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('model_version','prior_domain_skeleton_overlap','test','families','known_domain_formatting_controls')},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('artifact');p.add_argument('fresh_csv');p.add_argument('original_csv');p.add_argument('output')
    a=p.parse_args();evaluate(a.artifact,a.fresh_csv,a.original_csv,a.output)
