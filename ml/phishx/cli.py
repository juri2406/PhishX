import argparse
import json
from .features import analyze_url

def main():
    parser=argparse.ArgumentParser(description='PhishX offline detection tools')
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('analyze'); p.add_argument('url')
    p=sub.add_parser('prepare'); p.add_argument('csv'); p.add_argument('output'); p.add_argument('--seed',type=int,default=42)
    p=sub.add_parser('train'); p.add_argument('splits'); p.add_argument('output')
    p=sub.add_parser('predict'); p.add_argument('url'); p.add_argument('--model',required=True)
    args=parser.parse_args()
    try:
        if args.command=='analyze': result=analyze_url(args.url)
        elif args.command=='prepare':
            from .dataset import prepare
            result=prepare(args.csv,args.output,args.seed)
        elif args.command=='train':
            from .model import train
            result=train(args.splits,args.output)
        else:
            from .model import predict
            result=predict(args.url,args.model)
        print(json.dumps(result,indent=2,ensure_ascii=False))
    except (ValueError, FileNotFoundError) as exc:
        parser.exit(2,f'Error: {exc}\n')
