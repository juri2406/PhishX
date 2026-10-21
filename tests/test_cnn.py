"""Synthetic tests prove pipeline behavior, not phishing detection quality."""
import csv
import json
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip('torch')

from phishx.charcnn import CharacterTokenizer, CharCNN, CNNPredictor
from phishx.cascade import CascadePredictor, routing_mask
from phishx.cnn_workflow import checked_splits, select_gate, train_cnn, evaluate
from phishx.dataset import prepare
from phishx.model import train


def test_tokenizer_training_vocabulary_and_roundtrip():
    tokenizer = CharacterTokenizer.fit(['https://example.com'], 32)
    assert 'Ж' not in tokenizer.lookup
    encoded = tokenizer.encode(['https://example.com/Ж'])
    assert 1 in encoded
    assert np.array_equal(encoded, CharacterTokenizer(tokenizer.characters, 32).encode(['https://example.com/Ж']))
    assert encoded.dtype == np.int64
    with pytest.raises(ValueError):
        tokenizer.encode(['ftp://example.com'])


def test_head_tail_retains_payload_and_padding():
    tokenizer = CharacterTokenizer.fit(['https://example.com/' + 'a' * 80 + '?z=9'], 32)
    encoded = tokenizer.encode(['https://example.com/' + 'a' * 80 + '?z=9'])[0]
    assert list(encoded[-4:]) == [tokenizer.lookup[c] for c in '?z=9']
    assert tokenizer.encode(['a.co'])[0, -1] == 0


def test_cnn_gradient_and_padding_invariance():
    torch.manual_seed(3)
    model = CharCNN(20, channels=4, dropout=0).eval()
    first = torch.tensor([[2, 3, 4, 5, 6, 7, 8, 0, 0, 0]])
    longer = torch.nn.functional.pad(first, (0, 10))
    torch.testing.assert_close(model(first), model(longer))
    loss = torch.nn.functional.binary_cross_entropy_with_logits(model(first), torch.ones(1))
    loss.backward()
    assert torch.isfinite(model.output.weight.grad).all()
    assert torch.isfinite(model(torch.zeros((1, 10), dtype=torch.long))).all()


def test_lazy_cascade_only_escalates_uncertain_rows():
    class RF:
        def probabilities(self, urls):
            return np.array([.1, .4, .6, .9])
    class CNN:
        def probabilities(self, urls):
            assert urls == ['b', 'c']
            return np.array([.8, .2])
    predictor = CascadePredictor(RF(), CNN(), .4, .6)
    probability, paths = predictor.probabilities_with_paths(['a', 'b', 'c', 'd'])
    np.testing.assert_allclose(probability, [.1, .8, .2, .9])
    assert paths == ['classical', 'char_cnn', 'char_cnn', 'classical']
    assert not routing_mask([.5], .5, .5).any()
    with pytest.raises(ValueError):
        routing_mask([float('nan')], .4, .6)


def test_gate_retains_baseline_when_cnn_is_worse():
    selected, _, _ = select_gate([0, 1, 0, 1], np.array([.4, .6, .1, .9]), np.array([.9, .1, .9, .1]))
    assert selected['low'] == selected['high'] == .5


def test_gate_respects_targets():
    selected, _, _ = select_gate([0, 1, 0, 1], np.array([.6, .4, .1, .9]), np.array([.1, .9, .1, .9]), 1, 0)
    assert selected['metrics']['recall'] == 1
    assert selected['metrics']['false_positive_rate'] == 0
    with pytest.raises(ValueError, match='No validation gate'):
        select_gate([0, 1], np.array([.9, .1]), np.array([.9, .1]), 1, 0)


@pytest.fixture
def splits(tmp_path):
    source = tmp_path / 'synthetic.csv'
    with source.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=['url', 'label', 'source', 'collected_at'])
        writer.writeheader()
        for label in (0, 1):
            for i in range(45):
                writer.writerow(dict(url=f'https://{"ordinary" if label == 0 else "verify-account"}{i}.com/path',
                                     label=label, source='synthetic-engineering-test', collected_at='2026-10-21'))
    directory = tmp_path / 'splits'
    prepare(source, directory)
    return directory


def test_split_tampering_and_leakage_are_rejected(splits):
    from phishx.cascade import file_hash
    validation = splits / 'validation.csv'
    original = validation.read_text()
    validation.write_text(original + '\n')
    with pytest.raises(ValueError, match='checksum'):
        checked_splits(splits, ['train', 'validation'])
    validation.write_text((splits / 'train.csv').read_text())
    manifest = json.loads((splits / 'manifest.json').read_text())
    manifest['split_sha256']['validation'] = file_hash(validation)
    (splits / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='leakage'):
        checked_splits(splits, ['train', 'validation'])


def test_training_evaluation_roundtrip_and_artifact_integrity(splits, tmp_path, monkeypatch):
    rf_dir, run, results = tmp_path / 'rf', tmp_path / 'cnn', tmp_path / 'results'
    train(splits, rf_dir)
    original_open = Path.open
    def no_test_read(self, *args, **kwargs):
        if self.name == 'test.csv':
            raise AssertionError('CNN training opened test.csv')
        return original_open(self, *args, **kwargs)
    with monkeypatch.context() as context:
        context.setattr(Path, 'open', no_test_read)
        train_cnn(splits, rf_dir / 'classical.joblib', run, epochs=2, patience=1, max_length=64, batch_size=32)
    assert json.loads((run / 'training.json').read_text())['test_accessed'] is False
    predictor = CNNPredictor.load(run / 'charcnn.pt')
    probabilities = predictor.probabilities(['https://example.com'])
    assert 0 <= probabilities[0] <= 1
    report = evaluate(splits, rf_dir / 'classical.joblib', run, results, 'previously_evaluated', latency_samples=2)
    assert set(report['models']) == {'classical', 'char_cnn', 'cascade'}
    assert report['models']['cascade']['latency']['samples'] == 2
    assert (results / 'errors.json').is_file()
    with pytest.raises(ValueError, match='empty output'):
        evaluate(splits, rf_dir / 'classical.joblib', run, results, 'previously_evaluated', 2)
    with (run / 'charcnn.pt').open('ab') as stream:
        stream.write(b'tampered')
    with pytest.raises(ValueError, match='artifacts differ'):
        CascadePredictor.load(run / 'cascade.json', rf_dir / 'classical.joblib', run / 'charcnn.pt')
