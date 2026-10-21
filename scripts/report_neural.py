"""Post-freeze stress and CPU latency observations; no tuning or raw URL output."""
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import torch
from phishx.cascade import CascadePredictor
from phishx.model import load_rows
from phishx.robustness import variant,FAMILIES
from phishx.urls import InvalidURL
import idna


def report(directory,classical,splits,output):
    output=Path(output)
    if output.exists():raise ValueError('Use new output')
    torch.set_num_threads(4)
    cascade=CascadePredictor(directory,classical)
    result=json.loads((Path(directory)/'evaluation.json').read_text())
    rows=load_rows(Path(splits)/'final.csv')
    result['stress']={}
    for family in FAMILIES:
        original=[];altered=[]
        for row in rows:
            if row['label']!='1':continue
            try:
                changed=variant(row['url'],family)
                if changed:
                    cascade.analyze(changed);original.append(row['url']);altered.append(changed)
            except (InvalidURL,idna.IDNAError):continue
            if len(altered)==200:break
        original_prob,_,_,_=cascade.predict(original)
        probability,rf,_,_=cascade.predict(altered)
        cnn=np.array(cascade.cnn.probabilities(altered))
        result['stress'][family]={'rows':len(altered),'cascade_variant_recall':float((probability>=.5).mean()),'classical_variant_recall':float((rf>=.5).mean()),'cnn_variant_recall':float((cnn>=.5).mean()),'paired_original_cascade_recall':float((original_prob>=.5).mean()),'cascade_lost_detections':int(((original_prob>=.5)&(probability<.5)).sum())}
    # Previously observed public controls, not an independent test set.
    urls=['https://paypal.com/login','https://github.com/juri2406/PhishX','https://github.com/','https://www.w3.org/TR/2023/REC-WCAG22-20231005/','https://pаypal.com/login']
    final,rf,routed,_=cascade.predict(urls);cnn=cascade.cnn.probabilities(urls)
    result['known_controls']=[{'url':u,'classical_probability':float(a),'cnn_probability':float(b),'cascade_probability':float(c),'cnn_routed':bool(d)} for u,a,b,c,d in zip(urls,rf,cnn,final,routed)]
    timing={}
    for url in ('https://github.com/', 'https://example.com/'):
        cascade.predict([url]);values=[]
        for _ in range(30):
            start=perf_counter();_,_,r,_=cascade.predict([url]);values.append((perf_counter()-start)*1000)
        timing[url]={'samples_ms':values,'median_ms':float(np.median(values)),'p95_ms':float(np.percentile(values,95)),'cnn_routed':bool(r[0])}
    result['warm_cpu_latency']={'threads':4,'batch_size':1,'includes':'Shared parsing, numeric features, RF inference, gate and any routed CNN inference. Excludes SHAP/HTTP. Warm calls only.','controls':timing}
    result['stress_caveat']='200 paired offline manipulations per family on historical run06 final. No page visits; synthetic attack intent, not verified malicious deployments. No post-test tuning.'
    # Retain aggregate data and hashes, never dataset URL records.
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'stress':result['stress'],'controls':result['known_controls'],'latency':{u:{k:v for k,v in t.items() if k!='samples_ms'} for u,t in timing.items()}},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('directory','classical','splits','output'):p.add_argument(name)
    a=p.parse_args();report(a.directory,a.classical,a.splits,a.output)
