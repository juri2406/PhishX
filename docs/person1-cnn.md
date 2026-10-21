# Person 1: character CNN and cascade

Implemented in a workspace copy of C:/Users/MEGHA/PhishX on 21 October 2026.
The original checkout was not modified. GitHub was inaccessible, so this copy
has not been checked against the current remote branch. Existing milestone
reports are historical evidence; this change does not reinterpret their results.

## Implemented

- Character vocabulary fitted only on training URLs. PAD=0 and UNK=1.
- Shared URL validation; preserve raw Unicode, case and percent encoding.
- Default 512-character input, retaining head and tail when truncated.
- Embedding, parallel width 3/5/7 convolutions, global max pooling, dropout
  and binary classification. Padding windows are excluded from pooling.
- CPU deterministic training, train-only class weighting and validation-F1
  checkpoint selection with early stopping. No test data opened during training.
- RF-first inference, escalating only predictions inside the selected interval.
- Validation-only gate selection, including 0.4-0.6 and a no-escalation option.
  By default, require validation recall at least equal to RF and FPR no worse
  than RF, then maximize F1, breaking ties by lower FPR and less escalation.
- Separate frozen evaluation of RF, CNN and cascade: accuracy, precision,
  recall, F1, FPR, confusion matrix, Brier/log loss and probability bins;
  source/family breakdowns, escalation rate and local warmed CPU timings.
- Local errors.json lists false positives and false negatives for each model.
- Split checksums, recomputed domain/skeleton overlap checks, RF dataset
  lineage, frozen artifact hashes and parser/tokenizer compatibility checks.

## Install and run

From the repository root, using Python 3.10 or newer:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e '.[cnn]' pytest
.venv/Scripts/python.exe -m pytest tests/test_cnn.py -q
```

Recover the exact prepared train.csv, validation.csv, test.csv and manifest.json
for the RF, plus the trusted RF artifact. All three split checksums must match
the RF bundle. The current machine has neither run06 nor its datasets. Its
older run03 artifact cannot be substituted for run06 results. Do not bypass
lineage checks. For a new experiment, use the existing prepare/train tools
to produce a new RF and matching splits, keeping genuinely new final data
outside model selection.

```powershell
python -m phishx.cnn_workflow train --splits data/processed/experiment --classical artifacts/experiment/classical.joblib --output artifacts/cnn-run01
```

Optional flags: --epochs 20 --patience 4 --batch-size 128 --max-length 512
--seed 42 --min-recall 0.95 --max-fpr 0.03. The numeric targets here are
illustrations, not accepted project requirements. Agree targets with the team.
No eligible validation gate means a failed selection, with training history
retained for investigation. An equal-performing gate may retain RF entirely;
successful training alone is not evidence that CNN adds value.

Freeze the run before evaluating:

```powershell
python -m phishx.cnn_workflow evaluate --splits data/processed/experiment --classical artifacts/experiment/classical.joblib --run artifacts/cnn-run01 --output artifacts/cnn-evaluation01 --test-status previously_evaluated
```

Use fresh_holdout only when the team can establish the test data was reserved
before any selection or error review. Existing run03/run06 test sets have
already been evaluated; new code cannot make them untouched again. The flag
records the operator's provenance statement, not an automatic guarantee.
Do not tune on final errors and continue calling that set untouched. Review
validation errors for development; acquire another held-out set for later
final claims if test errors influence implementation. Output directories must
be empty to avoid replacing frozen evidence.

Artifacts: charcnn.pt, training.json, validation-errors.json, cascade.json. Evaluation outputs:
evaluation.json and errors.json (sensitive URL strings, keep local/ignored).
Latency includes parsing or tokenization and model execution, excludes network,
startup and SHAP, and reports batch throughput separately from individual
request p50/p95. Timings are measured on the current machine, not deployment.

## Person 2 handoff

```python
from phishx.cascade import CascadePredictor

predictor = CascadePredictor.load(
    'artifacts/cnn-run01/cascade.json',
    'artifacts/experiment/classical.joblib',
    'artifacts/cnn-run01/charcnn.pt',
)
result = predictor.predict('https://example.com')
```

Load once at application startup. This is an ML inference adapter; existing
backend, frontend and classical SHAP integration are unchanged. Person 2 must
integrate it into the application response contract and test concurrent scans.
CNN-routed results explicitly lack CNN attribution: RF SHAP must not be
presented as explaining the CNN verdict. Scores remain uncalibrated.

## Reliability work still requiring real data

Recover or collect matching datasets/artifacts; train on real labeled data;
agree recall/FPR/latency targets; compare the frozen models; investigate
validation false positives and misses by source and manipulation family;
run genuinely new final-domain/temporal and unseen-family evaluations.
Consider probability calibration using a separate development partition
before interpreting the routing probabilities as calibrated confidence.
Synthetic engineering tests are not evidence of phishing accuracy. Existing
source labels, convenience sampling and low benign-domain diversity remain
limitations. No live URL fetches are added by this work.
