"""Offline character CNN. Vocabulary is fitted on training URLs only."""
import hashlib
from pathlib import Path

import numpy as np
import torch
from torch import nn

from .urls import normalize_url


def url_text(url):
    # Validate with the shared parser, retaining Unicode and encoded attack evidence.
    return normalize_url(url).raw


class CharacterTokenizer:
    def __init__(self, characters, max_length=512):
        if not 8 <= max_length <= 2048:
            raise ValueError('max_length must be between 8 and 2048.')
        if len(set(characters)) != len(characters) or any(len(c) != 1 for c in characters):
            raise ValueError('Vocabulary must contain unique characters.')
        self.characters = list(characters)
        self.max_length = max_length
        self.lookup = {char: i + 2 for i, char in enumerate(characters)}

    @classmethod
    def fit(cls, urls, max_length=512):
        return cls(sorted({c for url in urls for c in url_text(url)}), max_length)

    def encode(self, urls):
        result = np.zeros((len(urls), self.max_length), dtype=np.int64)
        for row, url in enumerate(urls):
            text = url_text(url)
            # Preserve both hostname and trailing payload when a URL is too long.
            if len(text) > self.max_length:
                head = self.max_length // 2
                text = text[:head] + text[-(self.max_length - head):]
            result[row, :len(text)] = [self.lookup.get(c, 1) for c in text]
        return result

    def metadata(self):
        return dict(characters=self.characters, max_length=self.max_length,
                    pad_id=0, unknown_id=1, representation='validated-raw-head-tail-v1')


class CharCNN(nn.Module):
    def __init__(self, vocabulary_size, embedding_dim=32, channels=64, kernels=(3, 5, 7), dropout=.2):
        super().__init__()
        self.embedding = nn.Embedding(vocabulary_size, embedding_dim, padding_idx=0)
        self.convolutions = nn.ModuleList(nn.Conv1d(embedding_dim, channels, k) for k in kernels)
        self.dropout = nn.Dropout(dropout)
        self.output = nn.Linear(channels * len(kernels), 1)

    def forward(self, tokens):
        embedded = self.embedding(tokens).transpose(1, 2)
        pooled = []
        for conv in self.convolutions:
            activation = torch.relu(conv(embedded))
            # Ignore incomplete windows so extra right padding cannot change scores.
            valid = tokens.unfold(1, conv.kernel_size[0], 1).ne(0).all(-1)
            activation = activation.masked_fill(~valid[:, None, :], -torch.inf)
            values = activation.amax(dim=-1)
            pooled.append(torch.where(torch.isfinite(values), values, torch.zeros_like(values)))
        return self.output(self.dropout(torch.cat(pooled, dim=1))).squeeze(-1)


def source_hashes():
    return {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('charcnn.py', 'urls.py')}


class CNNPredictor:
    def __init__(self, model, tokenizer, metadata):
        self.model = model.eval()
        self.tokenizer = tokenizer
        self.metadata = metadata

    @classmethod
    def load(cls, path):
        checkpoint = torch.load(path, map_location='cpu', weights_only=True)
        if checkpoint.get('format') != 'phishx-charcnn-v1':
            raise ValueError('Unsupported CNN checkpoint.')
        if checkpoint['source_hashes'] != source_hashes():
            raise ValueError('CNN/parser source changed; retrain before inference.')
        metadata = checkpoint['tokenizer']
        if metadata.get('representation') != 'validated-raw-head-tail-v1':
            raise ValueError('Unsupported tokenizer representation.')
        tokenizer = CharacterTokenizer(metadata['characters'], metadata['max_length'])
        model = CharCNN(len(tokenizer.characters) + 2, **checkpoint['architecture'])
        model.load_state_dict(checkpoint['state_dict'])
        return cls(model, tokenizer, checkpoint)

    def probabilities(self, urls, batch_size=128):
        if batch_size < 1:
            raise ValueError('batch_size must be positive.')
        chunks = []
        with torch.inference_mode():
            for start in range(0, len(urls), batch_size):
                encoded = self.tokenizer.encode(urls[start:start + batch_size])
                chunks.append(torch.sigmoid(self.model(torch.from_numpy(encoded))).numpy())
        return np.concatenate(chunks).astype(float) if chunks else np.empty(0)
