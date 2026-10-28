"""Versioned character CNN using the existing canonical URL representation."""
import hashlib
import json
from pathlib import Path

import torch
from torch import nn
from .urls import normalize_url
from .model import extractor_hashes, resource_hashes

MAX_LENGTH = 512


def canonical_text(url):
    return normalize_url(url).canonical


def text_window(text):
    # Preserve both the authority and terminal path/query on long URLs.
    return text if len(text) <= MAX_LENGTH else text[:384] + text[-128:]


def vocabulary(urls):
    return sorted({c for url in urls for c in text_window(canonical_text(url))})


def encode(urls, characters):
    lookup = {c: i+2 for i,c in enumerate(characters)}  # 0 padding, 1 unknown
    result = torch.zeros((len(urls), MAX_LENGTH), dtype=torch.long)
    for i,url in enumerate(urls):
        values = [lookup.get(c, 1) for c in text_window(canonical_text(url))]
        result[i,:len(values)] = torch.tensor(values, dtype=torch.long)
    return result


class CharacterCNN(nn.Module):
    def __init__(self, vocabulary_size):
        super().__init__()
        self.embedding = nn.Embedding(vocabulary_size, 16, padding_idx=0)
        self.convolutions = nn.ModuleList([nn.Conv1d(16, 24, k) for k in (3,5,7)])
        self.classifier = nn.Sequential(nn.Linear(72,32), nn.ReLU(), nn.Dropout(.2), nn.Linear(32,1))

    def forward(self, tokens):
        embedded = self.embedding(tokens).transpose(1,2)
        pooled = [torch.relu(conv(embedded)).amax(dim=2) for conv in self.convolutions]
        return self.classifier(torch.cat(pooled,dim=1)).squeeze(1)


def code_hash():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


class CNNPredictor:
    def __init__(self, directory):
        directory = Path(directory)
        self.metadata = json.loads((directory/'cnn-metadata.json').read_text())
        meta = self.metadata
        if meta['architecture'] != 'charcnn-v1' or meta['code_sha256'] != code_hash():
            raise ValueError('CNN architecture/code mismatch')
        if meta['extractor_hashes'] != extractor_hashes() or meta['resource_hashes'] != resource_hashes():
            raise ValueError('CNN parser/resource mismatch')
        weights = directory/'charcnn.pt'
        if hashlib.sha256(weights.read_bytes()).hexdigest() != meta['weights_sha256']:
            raise ValueError('CNN weights checksum mismatch')
        self.characters = meta['characters']
        self.model = CharacterCNN(len(self.characters)+2)
        self.model.load_state_dict(torch.load(weights, map_location='cpu', weights_only=True))
        self.model.eval()
        self.version = meta['version']

    def probabilities(self, urls, batch_size=128):
        values = []
        with torch.inference_mode():
            for start in range(0,len(urls),batch_size):
                tokens = encode(urls[start:start+batch_size],self.characters)
                values.extend(torch.sigmoid(self.model(tokens)).tolist())
        return values
