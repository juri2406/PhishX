"""Versioned learned context inputs, using only a frozen public ranking snapshot."""
import math
import numpy as np
from .extended_features import EXTENDED_FEATURE_NAMES

CONTEXT_NAMES=('classical_output','neural_output','rank_present','log10_rank')+tuple(EXTENDED_FEATURE_NAMES)


def lookup_rank(analysis,ranks):
    parsed=analysis['normalized']
    return ranks.get(parsed['registrable_domain'],ranks.get(parsed['ascii_host'],1000001))


def context_matrix(classical,neural,analyses,ranks):
    rows=[]
    for rf,cnn,a in zip(classical,neural,analyses):
        rank=lookup_rank(a,ranks)
        rows.append([float(rf),float(cnn),float(rank<=1000000),math.log10(rank)]+[a['features'][name] for name in EXTENDED_FEATURE_NAMES])
    return np.asarray(rows,dtype=float)
