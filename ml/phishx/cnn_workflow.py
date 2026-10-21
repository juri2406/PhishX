"""Separate validation-only fitting from a frozen final evaluation."""
import argparse
import json
import platform
import random
from pathlib import Path
from time import perf_counter

import numpy as np

from .cascade import ClassicalPredictor, CascadePredictor, file_hash, routing_mask
from .dataset import domain_skeleton
from .model import load_rows, probability_report
from .urls import normalize_url


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def empty_output(path):
    path = Path(path)
    if path.exists() and any(path.iterdir()):
        raise ValueError('Choose an empty output directory; never overwrite a frozen run.')
    path.mkdir(parents=True, exist_ok=True)
    return path


def checked_splits(directory, names):
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    hashes = manifest.get('split_sha256', {})
    if set(hashes) != {'train', 'validation', 'test'}:
        raise ValueError('Manifest must record all three prepared split checksums.')
    rows = {}
    identities = {}
    for name in names:
        path = directory / f'{name}.csv'
        if file_hash(path) != hashes[name]:
            raise ValueError(f'{name} split checksum mismatch.')
        rows[name] = load_rows(path)
        if {r.get('label') for r in rows[name]} != {'0', '1'}:
            raise ValueError(f'{name} requires both binary labels.')
        identities[name] = {field: set() for field in ('domain', 'skeleton', 'canonical')}
        for row in rows[name]:
            if not row.get('group_domain'):
                raise ValueError('Use prepared splits with group_domain for every record.')
            url = normalize_url(row['url'])
            origin = normalize_url(row['group_domain']).registrable_domain
            identities[name]['domain'].update((url.registrable_domain, origin))
            identities[name]['skeleton'].update((domain_skeleton(url.registrable_domain), domain_skeleton(origin)))
            identities[name]['canonical'].add(url.canonical)
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            for field in identities[left]:
                if identities[left][field] & identities[right][field]:
                    raise ValueError(f'{field} leakage between {left} and {right}.')
    return rows, hashes


def require_lineage(bundle, hashes):
    if any(bundle.get('split_sha256', {}).get(name) != hashes[name] for name in hashes):
        raise ValueError('Random Forest must come from these exact prepared splits; retrain or recover its splits.')


def select_gate(labels, classical, cnn, min_recall=None, max_fpr=None):
    baseline = probability_report(labels, classical)
    min_recall = baseline['recall'] if min_recall is None else min_recall
    max_fpr = baseline['false_positive_rate'] if max_fpr is None else max_fpr
    if not 0 <= min_recall <= 1 or not 0 <= max_fpr <= 1:
        raise ValueError('Recall and false-positive targets must be in [0,1].')
    candidates = []
    for low, high in [(0.5, 0.5)] + [(lo, hi) for lo in (.2, .3, .4, .45) for hi in (.55, .6, .7, .8)]:
        mask = routing_mask(classical, low, high)
        report = probability_report(labels, np.where(mask, cnn, classical))
        candidates.append(dict(low=low, high=high, escalation_rate=float(mask.mean()), metrics=report,
                               eligible=report['recall'] >= min_recall and report['false_positive_rate'] <= max_fpr))
    eligible = [candidate for candidate in candidates if candidate['eligible']]
    if not eligible:
        raise ValueError('No validation gate meets the targets; no cascade was approved. Review validation errors.')
    selected = max(eligible, key=lambda c: (c['metrics']['f1'], -c['metrics']['false_positive_rate'], -c['escalation_rate']))
    return selected, candidates, dict(min_recall=min_recall, max_fpr=max_fpr)


def train_cnn(splits, classical_path, output, epochs=20, patience=4, batch_size=128,
              max_length=512, seed=42, min_recall=None, max_fpr=None):
    import torch
    from torch import nn
    from .charcnn import CharCNN, CharacterTokenizer, CNNPredictor, source_hashes
    if min(epochs, patience, batch_size) < 1:
        raise ValueError('epochs, patience and batch_size must be positive.')
    rows, hashes = checked_splits(splits, ['train', 'validation'])  # Never opens test.csv.
    classical = ClassicalPredictor(classical_path)
    require_lineage(classical.bundle, hashes)
    out = empty_output(output)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    urls = {name: [r['url'] for r in rs] for name, rs in rows.items()}
    labels = {name: np.array([int(r['label']) for r in rs]) for name, rs in rows.items()}
    tokenizer = CharacterTokenizer.fit(urls['train'], max_length)
    x = torch.from_numpy(tokenizer.encode(urls['train']))
    y = torch.tensor(labels['train'], dtype=torch.float32)
    architecture = dict(embedding_dim=32, channels=64, kernels=[3, 5, 7], dropout=.2)
    model = CharCNN(len(tokenizer.characters) + 2, **architecture)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=(y == 0).sum() / (y == 1).sum())
    optimizer = torch.optim.Adam(model.parameters(), lr=.001)
    predictor = CNNPredictor(model, tokenizer, {})
    best, stale, history = -1, 0, []
    metadata = dict(format='phishx-charcnn-v1', tokenizer=tokenizer.metadata(), architecture=architecture,
                    source_hashes=source_hashes(), split_sha256=hashes, seed=seed,
                    torch_version=str(torch.__version__), probability_calibrated=False,
                    classical_sha256=file_hash(classical_path), label_mapping={'benign': 0, 'phishing': 1})
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        order = torch.randperm(len(y))
        for start in range(0, len(y), batch_size):
            indices = order[start:start + batch_size]
            optimizer.zero_grad()
            loss = loss_fn(model(x[indices]), y[indices])
            loss.backward()
            optimizer.step()
            total_loss += float(loss.detach()) * len(indices)
        probabilities = predictor.probabilities(urls['validation'], batch_size)
        metrics = probability_report(labels['validation'], probabilities)
        history.append(dict(epoch=epoch, train_loss=total_loss / len(y), validation=metrics))
        if metrics['f1'] > best:
            best, stale = metrics['f1'], 0
            torch.save(dict(**metadata, selected_epoch=epoch, state_dict=model.state_dict()), out / 'charcnn.pt')
        else:
            stale += 1
        if stale >= patience:
            break
    frozen = CNNPredictor.load(out / 'charcnn.pt')
    cnn_prob = frozen.probabilities(urls['validation'])
    rf_prob = classical.probabilities(urls['validation'])
    write_json(out / 'training.json', dict(history=history, selected_epoch=frozen.metadata['selected_epoch'],
               split_sha256=hashes, test_accessed=False, selection='validation F1; earliest epoch wins ties',
               configuration=dict(epochs=epochs, patience=patience, batch_size=batch_size,
                                  max_length=max_length, seed=seed, learning_rate=.001,
                                  class_weight='training_negative_count / training_positive_count'),
               note='Raw model scores are uncalibrated. Test evaluation is a separate command.'))
    write_json(out / 'validation-errors.json', dict(
        classical=error_records(rows['validation'], rf_prob, ['classical'] * len(rf_prob)),
        char_cnn=error_records(rows['validation'], cnn_prob, ['char_cnn'] * len(cnn_prob))))
    selected, candidates, targets = select_gate(labels['validation'], rf_prob, cnn_prob, min_recall, max_fpr)
    config = dict(format='phishx-cascade-v1', low=selected['low'], high=selected['high'],
                  classical_sha256=file_hash(classical_path), cnn_sha256=file_hash(out / 'charcnn.pt'),
                  split_sha256=hashes, targets=targets, selected=selected, candidates=candidates,
                  status='validation_candidate' if selected['low'] < selected['high'] else 'classical_retained',
                  decision_threshold=.5, probability_calibrated=False)
    write_json(out / 'cascade.json', config)
    return dict(output=str(out), selected_epoch=frozen.metadata['selected_epoch'], gate=selected, status=config['status'])


def error_records(rows, probabilities, paths):
    return [dict(url=r['url'], label=int(r['label']), phishing_probability=float(p), model_used=path,
                 error='false_positive' if int(r['label']) == 0 else 'false_negative',
                 source=r.get('source'), family=r.get('family', 'original'))
            for r, p, path in zip(rows, probabilities, paths) if (p >= .5) != bool(int(r['label']))]


def evaluate(splits, classical_path, run, output, test_status, latency_samples=100):
    import torch
    from .charcnn import CNNPredictor
    if test_status not in ('previously_evaluated', 'fresh_holdout') or latency_samples < 1:
        raise ValueError('Declare test provenance and a positive latency sample count.')
    rows, hashes = checked_splits(splits, ['train', 'validation', 'test'])
    run = Path(run)
    config = json.loads((run / 'cascade.json').read_text())
    if hashes != config['split_sha256']:
        raise ValueError('Evaluation splits differ from frozen selection splits.')
    cascade = CascadePredictor.load(run / 'cascade.json', classical_path, run / 'charcnn.pt')
    require_lineage(cascade.classical.bundle, hashes)
    cnn = CNNPredictor.load(run / 'charcnn.pt')
    out = empty_output(output)
    test = rows['test']
    urls, labels = [r['url'] for r in test], [int(r['label']) for r in test]
    report = dict(test_status=test_status, split_sha256=hashes, models={},
                  environment=dict(platform=platform.platform(), python=platform.python_version(),
                                   torch=str(torch.__version__), torch_cpu_threads=torch.get_num_threads()),
                  frozen_config_sha256=file_hash(run / 'cascade.json'),
                  limitations=['Previously evaluated splits cannot support an untouched-test claim.',
                               'Validation targets do not guarantee test or deployment performance.',
                               'Scores are uncalibrated; latency includes parsing/tokenization on local CPU.'])
    all_errors = {}
    for name, predictor in [('classical', cascade.classical), ('char_cnn', cnn), ('cascade', cascade)]:
        predictor.probabilities(urls[:1])  # Explicit warmup excluded from timings.
        start = perf_counter()
        if name == 'cascade':
            probabilities, paths = cascade.probabilities_with_paths(urls)
        else:
            probabilities = predictor.probabilities(urls)
            paths = [name] * len(urls)
        batch_ms = 1000 * (perf_counter() - start) / len(urls)
        timings = []
        for url in urls[:latency_samples]:
            start = perf_counter()
            predictor.probabilities([url])
            timings.append(1000 * (perf_counter() - start))
        metrics = probability_report(labels, probabilities)
        metrics['latency'] = dict(batch_ms_per_url=batch_ms, single_url_p50_ms=float(np.median(timings)),
                                 single_url_p95_ms=float(np.percentile(timings, 95)), samples=len(timings), warmup_excluded=True)
        if name == 'cascade':
            metrics['escalation_rate'] = paths.count('char_cnn') / len(paths)
        for field in ('source', 'family'):
            metrics['by_' + field] = {}
            for value in sorted({r.get(field) or 'unspecified' for r in test}):
                mask = np.array([(r.get(field) or 'unspecified') == value for r in test])
                metrics['by_' + field][value] = probability_report(np.asarray(labels)[mask], probabilities[mask])
        report['models'][name] = metrics
        all_errors[name] = error_records(test, probabilities, paths)
    write_json(out / 'evaluation.json', report)
    write_json(out / 'errors.json', all_errors)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    train = sub.add_parser('train')
    train.add_argument('--splits', required=True)
    train.add_argument('--classical', required=True)
    train.add_argument('--output', required=True)
    for name, default in [('epochs', 20), ('patience', 4), ('batch-size', 128), ('max-length', 512), ('seed', 42)]:
        train.add_argument('--' + name, type=int, default=default)
    train.add_argument('--min-recall', type=float)
    train.add_argument('--max-fpr', type=float)
    final = sub.add_parser('evaluate')
    for name in ('splits', 'classical', 'run', 'output'):
        final.add_argument('--' + name, required=True)
    final.add_argument('--test-status', choices=['previously_evaluated', 'fresh_holdout'], required=True)
    final.add_argument('--latency-samples', type=int, default=100)
    args = vars(parser.parse_args())
    command = args.pop('command')
    args['classical_path'] = args.pop('classical')
    try:
        result = train_cnn(**args) if command == 'train' else evaluate(**args)
        print(json.dumps(result, indent=2, allow_nan=False))
    except (ValueError, FileNotFoundError) as exc:
        parser.exit(2, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
