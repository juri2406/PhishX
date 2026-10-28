"""CSV cleaning, provenance and connected domain/skeleton partitions."""
import csv
import hashlib
import json
from pathlib import Path
from collections import Counter
import idna
from .urls import normalize_url, InvalidURL, _EXTRACT
from .skeleton import skeleton

REQUIRED = {'url', 'label', 'source', 'collected_at'}


def domain_skeleton(domain):
    return skeleton(idna.decode(domain)) if ':' not in domain else domain


def prepare(input_path, output_dir, seed=42):
    from sklearn.model_selection import GroupShuffleSplit
    input_path = Path(input_path)
    out = Path(output_dir)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Choose an empty output directory to avoid stale split files.')
    with input_path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if not REQUIRED.issubset(reader.fieldnames or []):
            raise ValueError('CSV requires url,label,source,collected_at columns.')
        rows = list(reader)
    unique = {}
    rejected = []
    conflicts = set()
    duplicates = 0
    for index, row in enumerate(rows, 2):
        try:
            if row.get('label') not in ('0', '1') or not (row.get('source') or '').strip() or not (row.get('collected_at') or '').strip():
                raise ValueError('Label must be 0 or 1 and provenance fields must be populated.')
            u = normalize_url(row['url'])
            key = u.canonical
            if key in unique:
                if unique[key]['label'] != row['label']:
                    conflicts.add(key)
                else:
                    duplicates += 1
                continue
            if row.get('family', 'original') not in ('', 'original', 'fixture') and not row.get('group_domain'):
                raise ValueError('Synthetic variants require their original group_domain.')
            group = normalize_url(row['group_domain']).registrable_domain if row.get('group_domain') else u.registrable_domain
            unique[key] = dict(url=u.raw, canonical=key, label=row['label'], source=row['source'],
                               collected_at=row['collected_at'], group_domain=group,
                               family=row.get('family') or 'original',
                               actual_domain=u.registrable_domain,
                               domain_skeleton=domain_skeleton(u.registrable_domain),
                               known_suffix=bool(u.is_ip or _EXTRACT(u.ascii_host).suffix))
        except (InvalidURL, ValueError, TypeError) as exc:
            rejected.append({'line': index, 'reason': str(exc)})
    clean = [r for key, r in unique.items() if key not in conflicts]
    # Components join explicit origins, actual domains and exact Unicode skeletons.
    # This also prevents inconsistent explicit origin groups splitting one real domain.
    parent = {}
    def find(key):
        parent.setdefault(key, key)
        root = key
        while parent[root] != root:
            root = parent[root]
        while parent[key] != key:
            previous = key
            key = parent[key]
            parent[previous] = root
        return root
    def join(left, right):
        a, b = find(left), find(right)
        parent[max(a,b)] = min(a,b)
    for row in clean:
        origin = 'domain:' + row['group_domain']
        actual = 'domain:' + row['actual_domain']
        join(origin, actual)
        join(actual, 'skeleton:' + row['domain_skeleton'])
        join(origin, 'skeleton:' + domain_skeleton(row['group_domain']))
    for row in clean:
        row['group_domain'] = find('domain:' + row['group_domain']).removeprefix('domain:')
    groups = [r['group_domain'] for r in clean]
    if len(set(groups)) < 10:
        raise ValueError('Need at least 10 independent domain/skeleton groups.')
    train, held = next(GroupShuffleSplit(n_splits=1, test_size=.3, random_state=seed).split(clean, groups=groups))
    held_rows = [clean[i] for i in held]
    val_i, test_i = next(GroupShuffleSplit(n_splits=1, test_size=.5, random_state=seed).split(held_rows, groups=[r['group_domain'] for r in held_rows]))
    splits = {'train':[clean[i] for i in train], 'validation':[held_rows[i] for i in val_i], 'test':[held_rows[i] for i in test_i]}
    for name, records in splits.items():
        if {r['label'] for r in records} != {'0','1'}:
            raise ValueError(f'{name} lacks both classes. Add more independent examples or choose another seed.')
    overlaps = {}
    for field in ('group_domain','actual_domain','domain_skeleton','canonical'):
        values = [set(r[field] for r in records) for records in splits.values()]
        count = sum(len(a & b) for i,a in enumerate(values) for b in values[i+1:])
        if count:
            raise ValueError(f'{field} leakage across partitions')
        overlaps[field] = count
    out.mkdir(parents=True, exist_ok=True)
    split_hashes = {}
    for name, records in splits.items():
        path = out / f'{name}.csv'
        with path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0]))
            writer.writeheader(); writer.writerows(records)
        split_hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    provenance = input_path.with_suffix('.sources.json')
    manifest = dict(input_sha256=hashlib.sha256(input_path.read_bytes()).hexdigest(), seed=seed,
                    source_provenance=json.loads(provenance.read_text()) if provenance.exists() else None,
                    input_rows=len(rows), accepted_rows=len(clean), duplicates=duplicates,
                    conflicting_urls_removed=len(conflicts), rejected=rejected,
                    group_overlap=0, overlap_audit=overlaps, split_sha256=split_hashes,
                    unknown_suffix_rows=sum(not r['known_suffix'] for r in clean),
                    splits={name:dict(rows=len(rs), domains=len({r['actual_domain'] for r in rs}),
                                     groups=len({r['group_domain'] for r in rs}),
                                     labels=dict(Counter(r['label'] for r in rs))) for name,rs in splits.items()})
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest
