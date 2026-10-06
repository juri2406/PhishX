"""CSV cleaning and domain-separated partitions with provenance."""
import csv
import hashlib
import json
from pathlib import Path
from collections import Counter
from .urls import normalize_url, InvalidURL

REQUIRED = {'url', 'label', 'source', 'collected_at'}

def prepare(input_path, output_dir, seed=42):
    from sklearn.model_selection import GroupShuffleSplit
    input_path = Path(input_path); out = Path(output_dir)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Choose an empty output directory to avoid stale split files.')
    with input_path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if not REQUIRED.issubset(reader.fieldnames or []):
            raise ValueError('CSV requires url,label,source,collected_at columns.')
        rows = list(reader)
    unique = {}; rejected = []; conflicts = set(); duplicates = 0
    for index, row in enumerate(rows, 2):
        try:
            if row['label'] not in ('0', '1') or not row['source'].strip() or not row['collected_at'].strip():
                raise ValueError('Label must be 0 or 1 and provenance fields must be populated.')
            u = normalize_url(row['url']); key = u.canonical
            if key in unique:
                if unique[key]['label'] != row['label']:
                    conflicts.add(key)
                else: duplicates += 1
                continue
            # Set group_domain to the original base domain for generated variants.
            group = normalize_url(row['group_domain']).registrable_domain if row.get('group_domain') else u.registrable_domain
            unique[key] = dict(url=u.raw, canonical=key, label=row['label'], source=row['source'],
                               collected_at=row['collected_at'], group_domain=group,
                               family=row.get('family') or 'original')
        except (InvalidURL, ValueError) as exc:
            rejected.append({'line': index, 'reason': str(exc)})
    clean = [r for key, r in unique.items() if key not in conflicts]
    if len({r['group_domain'] for r in clean}) < 10:
        raise ValueError('Need at least 10 domain groups for train/validation/test splits.')
    groups = [r['group_domain'] for r in clean]
    train, held = next(GroupShuffleSplit(n_splits=1, test_size=.3, random_state=seed).split(clean, groups=groups))
    held_rows = [clean[i] for i in held]
    val_i, test_i = next(GroupShuffleSplit(n_splits=1, test_size=.5, random_state=seed).split(held_rows, groups=[r['group_domain'] for r in held_rows]))
    splits = {'train':[clean[i] for i in train], 'validation':[held_rows[i] for i in val_i], 'test':[held_rows[i] for i in test_i]}
    for name, records in splits.items():
        if {r['label'] for r in records} != {'0','1'}:
            raise ValueError(f'{name} lacks both classes. Add more independent examples or choose another seed.')
    domain_sets = [set(r['group_domain'] for r in records) for records in splits.values()]
    assert all(not a & b for i,a in enumerate(domain_sets) for b in domain_sets[i+1:])
    out.mkdir(parents=True, exist_ok=True)
    for name, records in splits.items():
        with (out / f'{name}.csv').open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0])); writer.writeheader(); writer.writerows(records)
    manifest = dict(input_sha256=hashlib.sha256(input_path.read_bytes()).hexdigest(), seed=seed,
                    input_rows=len(rows), accepted_rows=len(clean), duplicates=duplicates,
                    conflicting_urls_removed=len(conflicts), rejected=rejected,
                    group_overlap=0, splits={name:dict(rows=len(rs), domains=len({r['group_domain'] for r in rs}), labels=dict(Counter(r['label'] for r in rs))) for name,rs in splits.items()})
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2))
    return manifest
