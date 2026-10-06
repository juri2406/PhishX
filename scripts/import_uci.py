"""Import a reproducible URL-only subset from the official UCI PhiUSIIL ZIP."""
import argparse
import csv
import hashlib
import io
import json
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

DATASET_URL = 'https://archive.ics.uci.edu/dataset/967/phiusil-phishing-url-dataset'
DOWNLOAD_URL = 'https://archive.ics.uci.edu/static/public/967/phiusiil%2Bphishing%2Burl%2Bdataset.zip'


def import_uci(archive, output, per_class=5000, seed=42, exclude_csv=None):
    archive, output = Path(archive), Path(output)
    if per_class < 1:
        raise ValueError('per_class must be positive')
    if output.exists() or output.with_suffix('.sources.json').exists():
        raise ValueError('Choose a new output filename')
    rng = random.Random(seed)
    buckets = {0: [], 1: []}
    seen = Counter()
    exclusions = set()
    excluded_rows = invalid_rows = 0
    if exclude_csv:
        from phishx.urls import normalize_url, InvalidURL
        from phishx.dataset import domain_skeleton
        with Path(exclude_csv).open(encoding='utf-8', newline='') as excluded_file:
            for row in csv.DictReader(excluded_file):
                try:
                    exclusions.add(domain_skeleton(normalize_url(row['url']).registrable_domain))
                except InvalidURL:
                    continue
    with ZipFile(archive) as z:
        names = [n for n in z.namelist() if n.endswith('.csv')]
        if len(names) != 1:
            raise ValueError('Expected exactly one dataset CSV in the archive')
        member = names[0]
        with z.open(member) as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig', newline=''))
            if not {'URL', 'label'}.issubset(reader.fieldnames or []):
                raise ValueError('Expected UCI URL and label columns')
            for index, record in enumerate(reader, 2):
                # UCI 1=legitimate, 0=phishing; PhishX uses the inverse.
                original_label = int(record['label'])
                if original_label not in (0, 1):
                    raise ValueError('Unexpected UCI label')
                label = 1 - original_label
                if exclude_csv:
                    try:
                        normalized = normalize_url(record['URL'])
                        if domain_skeleton(normalized.registrable_domain) in exclusions:
                            excluded_rows += 1
                            continue
                    except InvalidURL:
                        invalid_rows += 1
                        continue
                row = dict(url=record['URL'], label=label,
                           source=f'uci-967:line-{index}', collected_at='unknown',
                           group_domain='', family='original')
                seen[label] += 1
                if len(buckets[label]) < per_class:
                    buckets[label].append(row)
                else:
                    replacement = rng.randrange(seen[label])
                    if replacement < per_class:
                        buckets[label][replacement] = row
    rows = buckets[0] + buckets[1]
    if min(len(buckets[0]), len(buckets[1])) < per_class:
        raise ValueError('Not enough rows in one class')
    rng.shuffle(rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    manifest = dict(dataset_url=DATASET_URL, download_url=DOWNLOAD_URL,
                    citation='Prasad, A. and Chandra, S. (2024). PhiUSIIL Phishing URL (Website). UCI Machine Learning Repository. https://doi.org/10.1016/j.cose.2023.103545',
                    license='CC BY 4.0', license_url='https://creativecommons.org/licenses/by/4.0/',
                    donation_date='2024-03-03', row_collection_dates='not provided by source',
                    downloaded_archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                    member=member, imported_at=datetime.now(timezone.utc).isoformat(),
                    sampling='deterministic per-class reservoir sampling before cleaning',
                    seed=seed, per_class=per_class, source_counts=dict(seen),
                    excluded_prior_rows=excluded_rows, invalid_rows_excluded=invalid_rows,
                    exclusion_csv_sha256=hashlib.sha256(Path(exclude_csv).read_bytes()).hexdigest() if exclude_csv else None,
                    imported_counts={label:len(records) for label,records in buckets.items()},
                    input_features_used=['URL'], label_mapping={'uci_0':1,'uci_1':0},
                    limitation='Historical labels inherited from UCI; current site status is not verified. Class-balanced sample is not real-world prevalence.')
    output.with_suffix('.sources.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive'); p.add_argument('output')
    p.add_argument('--per-class', type=int, default=5000)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--exclude-csv', help='Exclude all domains/skeletons used in a previous run')
    args = p.parse_args()
    print(json.dumps(import_uci(args.archive,args.output,args.per_class,args.seed,args.exclude_csv),indent=2))

if __name__ == '__main__':
    main()
