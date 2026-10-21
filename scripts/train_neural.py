"""Train/select on development data; freeze weights and gate before test loading."""
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset
from phishx.charcnn import CharacterCNN, CNNPredictor, encode, vocabulary, code_hash
from phishx.model import load_rows, load_bundle, extractor_hashes, resource_hashes, probability_report
from phishx.extended_features import analyze_extended


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def balanced(report): return (report['recall']+1-report['false_positive_rate'])/2


def train(splits, output, classical, holdout, epochs=8):
    splits,output,holdout = Path(splits),Path(output),Path(holdout)
    if output.exists(): raise ValueError('Use a new artifact directory')
    torch.set_num_threads(4);torch.manual_seed(42);np.random.seed(42)
    torch.use_deterministic_algorithms(True)
    manifest=json.loads((splits/'manifest.json').read_text())
    frozen_holdout=json.loads((holdout/'manifest.json').read_text())
    if digest(holdout/'holdout.csv') != frozen_holdout['holdout_sha256']: raise ValueError('Holdout changed')
    rows={name:load_rows(splits/f'{name}.csv') for name in ('train','selection')}
    for name in rows:
        if digest(splits/f'{name}.csv') != manifest['split_sha256'][name]: raise ValueError('Split changed')
    for field in ('canonical','actual_domain','domain_skeleton','group_domain'):
        if {r[field] for r in rows['train']} & {r[field] for r in rows['selection']}: raise ValueError('Development leakage')
    characters=vocabulary([r['url'] for r in rows['train']])
    xs={name:encode([r['url'] for r in rs],characters) for name,rs in rows.items()}
    ys={name:np.array([int(r['label']) for r in rs]) for name,rs in rows.items()}
    weights=torch.tensor([3. if r['source'].startswith('official-navigation:') else 1. for r in rows['train']])
    loader=DataLoader(TensorDataset(xs['train'],torch.tensor(ys['train'],dtype=torch.float32),weights),batch_size=128,shuffle=True,generator=torch.Generator().manual_seed(42))
    model=CharacterCNN(len(characters)+2)
    optimizer=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.0001)
    criterion=torch.nn.BCEWithLogitsLoss(reduction='none')
    output.mkdir(parents=True)
    history=[];best=-1.;start=perf_counter()
    def probs(tokens):
        model.eval()
        with torch.inference_mode(): return np.concatenate([torch.sigmoid(model(tokens[i:i+128])).numpy() for i in range(0,len(tokens),128)])
    for epoch in range(epochs):
        model.train();loss_sum=0.
        for tokens,labels,weight in loader:
            optimizer.zero_grad();loss=(criterion(model(tokens),labels)*weight).mean();loss.backward();optimizer.step();loss_sum+=float(loss.detach())*len(labels)
        selection=probability_report(ys['selection'],probs(xs['selection']))
        history.append({'epoch':epoch+1,'training_loss':loss_sum/len(rows['train']),'selection':selection})
        print(json.dumps({'epoch':epoch+1,'selection_balanced_accuracy':balanced(selection),'loss':history[-1]['training_loss']}),flush=True)
        if balanced(selection)>best:
            best=balanced(selection);best_epoch=epoch+1;torch.save(model.state_dict(),output/'charcnn.pt')
    model.load_state_dict(torch.load(output/'charcnn.pt',weights_only=True));model.eval()
    selection_cnn=probs(xs['selection'])
    bundle=load_bundle(classical)
    if bundle.get('feature_profile')!='extended-v1': raise ValueError('Expected v6 extended baseline')
    features=[analyze_extended(r['url'])['features'] for r in rows['selection']]
    classical_probs=bundle['model'].predict_proba([[f[n] for n in bundle['feature_names']] for f in features])[:,1]
    candidates=[]
    for lower,upper in ((.3,.7),(.2,.8),(.1,.9)):
        mask=(classical_probs>=lower)&(classical_probs<=upper)
        for weight in (.5,1.):
            prob=classical_probs.copy();prob[mask]=(1-weight)*prob[mask]+weight*selection_cnn[mask]
            report=probability_report(ys['selection'],prob)
            candidates.append({'lower':lower,'upper':upper,'cnn_weight':weight,'routed_fraction':float(mask.mean()),'selection':report})
    chosen=max(candidates,key=lambda r:(balanced(r['selection']),-r['routed_fraction']))
    version='charcnn-v1-'+digest(output/'charcnn.pt')[:12]
    meta={'architecture':'charcnn-v1','version':version,'characters':characters,'code_sha256':code_hash(),'weights_sha256':digest(output/'charcnn.pt'),
          'extractor_hashes':extractor_hashes(),'resource_hashes':resource_hashes(),'torch_version':str(torch.__version__),'seed':42,'best_epoch':best_epoch,
          'max_length':512,'long_url_policy':'First 384 and last 128 canonical Unicode code points','probability_calibrated':False,
          'development_sha256':{name:manifest['split_sha256'][name] for name in rows},'holdout_sha256':frozen_holdout['holdout_sha256']}
    policy={k:chosen[k] for k in ('lower','upper','cnn_weight')}
    policy.update(version='cascade-v1-'+digest(output/'charcnn.pt')[:12],cnn_version=version,classical_sha256=digest(classical),probability_calibrated=False,
                  routing_policy='Inclusive RF uncertainty interval; convex blend inside gate, unchanged RF outside. Gate/weight selected only on selection set.')
    (output/'cnn-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (output/'cascade-policy.json').write_text(json.dumps(policy,indent=2)+'\n')
    report={'metadata':meta,'cascade_policy':policy,'epochs':history,'cascade_candidates':candidates,'training_seconds':perf_counter()-start,
            'selection_classical':probability_report(ys['selection'],classical_probs),'selection_cnn':probability_report(ys['selection'],selection_cnn),
            'selected_cascade_selection':chosen['selection'],'fresh_holdout_manifest':frozen_holdout,
            'policy':'Weights, vocabulary, epoch and cascade gate frozen before loading either evaluation CSV. No post-test tuning.'}
    (output/'pre-evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
    from phishx.cascade import CascadePredictor
    cascade=CascadePredictor(output,classical)
    for name,path in [('retrospective_run06',splits/'final.csv'),('fresh_historical_uci',holdout/'holdout.csv')]:
        expected = manifest['split_sha256']['final'] if name == 'retrospective_run06' else frozen_holdout['holdout_sha256']
        if digest(path) != expected: raise ValueError('Evaluation data changed after freeze')
        rs=load_rows(path);urls=[r['url'] for r in rs];y=[int(r['label']) for r in rs]
        final,rf,routed,_=cascade.predict(urls);cnn=np.array(cascade.cnn.probabilities(urls))
        report[name]={'rows_sha256':digest(path),'classical':probability_report(y,rf),'cnn':probability_report(y,cnn),'cascade':probability_report(y,final),'routed_fraction':float(routed.mean())}
    report['promotion_decision']='Research candidate only; compare measured errors, source shift and calibration before changing served model.'
    (output/'evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('retrospective_run06','fresh_historical_uci')},indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('splits');p.add_argument('output');p.add_argument('classical');p.add_argument('holdout');p.add_argument('--epochs',type=int,default=8)
    a=p.parse_args();train(a.splits,a.output,a.classical,a.holdout,a.epochs)
