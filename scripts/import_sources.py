"""Convert local source exports into the training CSV; never visits URLs.
PhishTank JSON contains url/verified/online. OpenPhish is one URL per line.
Tranco is rank,domain CSV (benign candidates require manual review).
"""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--phishing',type=Path,required=True)
parser.add_argument('--format',choices=['phishtank','openphish'],required=True)
parser.add_argument('--benign',type=Path,required=True,help='Reviewed rank,domain CSV')
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--benign-reviewed',action='store_true')
args=parser.parse_args()
if not args.benign_reviewed:
    parser.error('Review the benign candidates, then pass --benign-reviewed. Top-site ranking alone is not a verified label.')
if args.output.exists() or args.output.with_suffix('.sources.json').exists():
    parser.error('Choose a new output filename.')
collected=datetime.now(timezone.utc).isoformat()
rows=[]
if args.format=='phishtank':
    records=json.loads(args.phishing.read_text(encoding='utf-8'))
    for record in records:
        if str(record.get('verified','')).lower() in ('yes','true') and str(record.get('online','')).lower() in ('yes','true'):
            rows.append([record['url'],1,'phishtank:'+str(record.get('phish_id','unknown')),collected,'','original'])
else:
    for line in args.phishing.read_text(encoding='utf-8').splitlines():
        if line.strip():rows.append([line.strip(),1,'openphish:'+args.phishing.name,collected,'','original'])
with args.benign.open(encoding='utf-8-sig',newline='') as f:
    for record in csv.reader(f):
        if len(record)!=2 or not record[0].isdigit():parser.error('Benign CSV must contain rank,domain rows without a header.')
        rows.append(['https://'+record[1].strip()+'/',0,'reviewed-tranco:'+args.benign.name,collected,'','original'])
args.output.parent.mkdir(parents=True,exist_ok=True)
with args.output.open('w',newline='',encoding='utf-8') as f:
    writer=csv.writer(f);writer.writerow(['url','label','source','collected_at','group_domain','family']);writer.writerows(rows)
manifest={'imported_at':collected,'phishing_format':args.format,'benign_reviewed':True,'rows':len(rows),
          'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (args.phishing,args.benign)}}
args.output.with_suffix('.sources.json').write_text(json.dumps(manifest,indent=2))
print(f'Imported {len(rows)} records into {args.output}')
