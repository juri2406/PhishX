"""Frozen-model URL-string stress tests; no URLs are visited or deployed."""
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, unquote
import idna
from .urls import normalize_url, InvalidURL
from .features import analyze_url, FEATURE_NAMES
from .model import load_bundle, load_rows, probability_report

FAMILIES = ('homoglyph','subdomain','percent_encoding')
HOMOGLYPHS = {'a':'а','c':'с','e':'е','o':'о','p':'р','x':'х','y':'у'}


def variant(url, family):
    parsed = normalize_url(url)
    parts = urlsplit(parsed.canonical)
    if family == 'percent_encoding':
        path=parts.path
        index=next((i for i,c in enumerate(path) if c.isascii() and c.isalnum()),None)
        if index is None:
            return None
        modified=path[:index]+'%'+format(ord(path[index]),'02X')+path[index+1:]
        assert unquote(modified)==unquote(path)
        return urlunsplit(parts._replace(path=modified))
    if parsed.is_ip or parsed.has_userinfo or parts.port is not None:
        return None
    if family == 'subdomain':
        host='paypal.'+parsed.ascii_host
        if len(host)>253:
            return None
        result=urlunsplit(parts._replace(netloc=host))
        # PSL private suffixes still refer to the same underlying tenant domain.
        if normalize_url(result).registrable_domain != parsed.registrable_domain:
            return None
        return result
    if family == 'homoglyph':
        labels=parsed.unicode_host.split('.')
        # Replace a character in the domain label, preserving the suffix.
        target=parsed.domain_label
        index=next((i for i,c in enumerate(target) if c in HOMOGLYPHS),None)
        if index is None:
            return None
        changed=target[:index]+HOMOGLYPHS[target[index]]+target[index+1:]
        position=len(parsed.subdomain.split('.')) if parsed.subdomain else 0
        labels[position]=changed
        host='.'.join(labels)
        idna.encode(host,uts46=True,transitional=False)
        return urlunsplit(parts._replace(netloc=host))
    raise ValueError('Unknown manipulation family')


def evaluate_robustness(split_dir, artifact, output_dir, per_family=200):
    if per_family < 1:
        raise ValueError('per_family must be positive')
    bundle=load_bundle(artifact); model=bundle['model']
    split_dir=Path(split_dir); out=Path(output_dir)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Choose an empty robustness output directory')
    manifest=json.loads((split_dir/'manifest.json').read_text())
    for name in ('train','validation','test'):
        expected=bundle.get('split_sha256',{}).get(name)
        actual=hashlib.sha256((split_dir/f'{name}.csv').read_bytes()).hexdigest()
        if not expected or expected != actual:
            raise ValueError('Robustness data must match the frozen artifact splits')
    train_rows=load_rows(split_dir/'train.csv')
    if any(r['family'] not in ('original','fixture') for r in train_rows):
        raise ValueError('This evaluation expects no generated-family training augmentation')
    test_rows=load_rows(split_dir/'test.csv')
    report=dict(model_version=bundle['version'],per_family_limit=per_family,
                augmentation_used=False, reserved_generated_family='homoglyph',
                families={},source_input_sha256=manifest['input_sha256'],
                caveat='Synthetic offline URL-string perturbations, not verified live phishing pages. Homoglyph domains change the host; labels reflect attack intent only. No claim that a family is absent naturally from source data.')
    records=[]
    for family in FAMILIES:
        pairs=[]; skipped=0
        for row in test_rows:
            if row['label']!='1':
                continue
            try:
                changed=variant(row['url'],family)
                if not changed or changed==row['url']:
                    skipped+=1; continue
                features=analyze_url(changed)['features']
            except (InvalidURL,idna.IDNAError):
                skipped+=1; continue
            original_features=analyze_url(row['url'])['features']
            pairs.append((row,changed,original_features,features))
            if len(pairs)>=per_family:
                break
        if not pairs:
            report['families'][family]=dict(rows=0,skipped_before_limit=skipped,recall=None)
            continue
        original=model.predict_proba([[p[2][name] for name in FEATURE_NAMES] for p in pairs])[:,1]
        altered=model.predict_proba([[p[3][name] for name in FEATURE_NAMES] for p in pairs])[:,1]
        family_result=probability_report([1]*len(pairs),altered)
        detected=sum(p>=.5 for p in original)
        family_result.update(skipped_before_limit=skipped,paired_original_recall=float(detected/len(pairs)),
                             lost_detections=int(sum(a>=.5 and b<.5 for a,b in zip(original,altered))),
                             retained_detected_fraction=float(sum(a>=.5 and b>=.5 for a,b in zip(original,altered))/detected) if detected else None)
        report['families'][family]=family_result
        for pair,a,b in zip(pairs,original,altered):
            row,changed,_,_=pair
            records.append(dict(family=family,source_url=row['url'],variant=changed,
                                group_domain=row['group_domain'],original_probability=float(a),variant_probability=float(b)))
    out.mkdir(parents=True,exist_ok=True)
    (out/'robustness.json').write_text(json.dumps(report,indent=2)+'\n')
    if records:
        with (out/'variants.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    return report
