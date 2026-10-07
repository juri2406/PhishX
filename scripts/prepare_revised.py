"""Freeze development/calibration/final groups before revised model training."""
import argparse
import bz2
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from phishx.dataset import prepare, domain_skeleton
from phishx.model import load_rows
from phishx.urls import normalize_url, InvalidURL


def write_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def prepare_revised(out, round_number=4):
    out = Path(out)
    if out.exists(): raise ValueError('Choose a new split directory')
    prior_paths = ['data/raw/uci_sample.csv', 'data/raw/uci_fresh_test.csv']
    prior = set()
    for path in prior_paths:
        for row in load_rows(path):
            try: prior.add(domain_skeleton(normalize_url(row['url']).registrable_domain))
            except InvalidURL: pass
    # Previously observed controls are development diagnostics, never final evidence.
    prior.update(domain_skeleton(host) for host in ('paypal.com','github.com'))
    if round_number >= 5:
        for previous in range(4,round_number):
            for name in ('train','selection','calibration_fit','calibration_review','final'):
                prior.update(r['domain_skeleton'] for r in load_rows(f'data/processed/revised-run{previous:02d}/{name}.csv'))
    fields = ['url','label','source','collected_at','group_domain','family']
    historical = (load_rows('data/processed/uci-run02/train.csv') + load_rows('data/processed/uci-run02/validation.csv')) if round_number == 4 else sum((load_rows(f'data/processed/revised-run{round_number-1:02d}/{name}.csv') for name in ('train','selection','calibration_fit','calibration_review','final')), [])
    rows = [{key:r.get(key,'') for key in fields} for r in historical]
    nav_path = Path('data/raw/official-navigation-20261007.csv' if round_number == 4 else f'data/raw/official-navigation-v{round_number}-20261007.csv')
    nav_manifest = json.loads(nav_path.with_suffix('.sources.json').read_text())
    reviewed = {s['seed'] for s in nav_manifest['sources'] if s.get('status') == 200 and s.get('title')}
    nav = [r for r in load_rows(nav_path) if r['source'].removeprefix('official-navigation:') in reviewed]
    rows += [{key:r.get(key,'') for key in fields} for r in nav]
    feed = Path('data/raw/phishtank-20261007.json.bz2')
    phishing = json.loads(bz2.decompress(feed.read_bytes()))
    recent = [r for r in phishing if r.get('verified')=='yes' and r.get('online')=='yes'
              and ('2026-09-07' if round_number == 4 else ('2026-08-08' if round_number == 5 else '2026-07-09')) <= r['verification_time'] < ('2026-10-08' if round_number == 4 else ('2026-09-07' if round_number == 5 else '2026-08-08'))]
    counts = Counter(); skipped = 0
    for row in sorted(recent, key=lambda r:int(r['phish_id'])):
        try:
            parsed = normalize_url(row['url']); group = domain_skeleton(parsed.registrable_domain)
        except InvalidURL:
            skipped += 1; continue
        if counts[group] >= 20: continue
        counts[group] += 1
        rows.append(dict(url=row['url'], label='1',source='phishtank:id-'+str(row['phish_id']),
                         collected_at=row['verification_time'], group_domain='',family='original'))
    # Reuse the shared deduplication, conflict and connected-group implementation.
    source = Path(f'data/raw/revised-input-v{round_number}-20261007.csv')
    if source.exists(): raise ValueError('Revised input already exists')
    write_csv(source, rows)
    cleaning = Path(f'work/revised-cleaning-v{round_number}-20261007')
    clean_manifest = prepare(source, cleaning, seed=20261007)
    clean = sum((load_rows(cleaning/f'{name}.csv') for name in ('train','validation','test')), [])
    partitions = {name:[] for name in ('train','selection','calibration_fit','calibration_review','final')}
    group_rows = {}
    for row in clean: group_rows.setdefault(row['group_domain'], []).append(row)
    for group, records in sorted(group_rows.items()):
        prior_seen = any(r['domain_skeleton'] in prior for r in records)
        external_only = all(not r['source'].startswith('uci-') for r in records)
        holdout_bucket = int(hashlib.sha256(('final-v'+str(round_number)+':'+group).encode()).hexdigest()[:8],16)%100
        if external_only and not prior_seen and holdout_bucket < 25:
            name='final'
        else:
            bucket=int(hashlib.sha256(('development-v'+str(round_number)+':'+group).encode()).hexdigest()[:8],16)%100
            name='train' if bucket<70 else 'selection' if bucket<80 else 'calibration_fit' if bucket<90 else 'calibration_review'
            if group in ('paypal.com','github.com','w3.org'): name='train'
        partitions[name] += records
    for name, records in partitions.items():
        if {r['label'] for r in records} != {'0','1'}:
            raise ValueError(name+' lacks a class; do not inspect final predictions or tune partition seeds')
    audit={}
    for field in ('canonical','group_domain','actual_domain','domain_skeleton'):
        groups=[{r[field] for r in records} for records in partitions.values()]
        overlap=sum(len(a&b) for i,a in enumerate(groups) for b in groups[i+1:])
        if overlap: raise ValueError(field+' leakage')
        audit[field]=overlap
    assert not {r['domain_skeleton'] for r in partitions['final']} & prior
    out.mkdir(parents=True)
    for name, records in partitions.items(): write_csv(out/f'{name}.csv',records)
    manifest={'selection_policy':'Deterministic SHA256 connected-group split fixed before training. New external groups: 25% final. Other groups: 70/10/10/10 train/selection/calibration fit/calibration review. Previously observed PayPal/GitHub/W3 diagnostic groups forced into training.',
              'final_policy':'No domains/skeletons from either previously observed UCI sample. Final is opened only after artifact freeze.',
              'cleaning':clean_manifest,'overlap_audit':audit,'final_prior_overlap':0,
              'phishtank':{'url':'https://data.phishtank.com/data/online-valid.json.bz2','sha256':hashlib.sha256(feed.read_bytes()).hexdigest(),
                          'feed_rows':len(phishing),'recent_rows':len(recent),'recent_invalid':skipped,
                          'date_filter':('2026-09-07 <= verification_time < 2026-10-08' if round_number == 4 else ('2026-08-08 <= verification_time < 2026-09-07' if round_number == 5 else '2026-07-09 <= verification_time < 2026-08-08'))+'; verified=yes; online=yes',
                          'cap':'20 URLs per exact domain skeleton; no target pages fetched','date_basis':'collected_at records source verification time, not original URL creation time'},
              'benign_navigation':{'sha256':hashlib.sha256(nav_path.read_bytes()).hexdigest(),'accepted_seed_titles':[{'seed':s['seed'],'title':s['title'],'rows':len(s['urls'])} for s in nav_manifest['sources'] if s['seed'] in reviewed],
                                   'basis':nav_manifest['label_basis'],'limitation':nav_manifest['limitation']},
              'round':round_number, 'historical':('Only old UCI train and validation rows reused. Old UCI test and fresh 4000 rows excluded from training; their groups excluded from final.' if round_number == 4 else 'All previously observed partitions may enter development. Its final is no longer untouched and is not reused as final evidence. Old UCI test/fresh groups and all previous revision groups are excluded from new final.'),
              'splits':{name:{'rows':len(rs),'labels':dict(Counter(r['label'] for r in rs)), 'groups':len({r['group_domain'] for r in rs}),
                              'source_counts':dict(Counter(r['source'].split(':')[0] for r in rs))} for name,rs in partitions.items()},
              'split_sha256':{name:hashlib.sha256((out/f'{name}.csv').read_bytes()).hexdigest() for name in partitions}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'splits':manifest['splits'],'overlap_audit':audit,'final_prior_overlap':0},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('output'); p.add_argument('--round', type=int, choices=(4,5,6), default=4)
    a=p.parse_args(); prepare_revised(a.output,a.round)
