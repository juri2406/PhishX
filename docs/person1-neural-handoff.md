# Person 1 neural research handoff — 21 October 2026

The remaining character-CNN and uncertainty-cascade implementation, training,
comparison, string stress tests and provider handoff are implemented. **The
candidate is not promoted:** broader-source false positives regress substantially.
The classical v6 provider remains the default. This is a completed research
experiment, not evidence of production readiness or universal detection quality.

## Frozen implementation

- Existing shared URL normalization, numeric features and Unicode brand resources
  are unchanged. No alternate backend training parser and no live-signal inputs.
- Canonical URL Unicode code points; vocabulary learned only from training rows.
  Padding 0, unknown 1. Maximum 512 characters; long strings retain the first 384
  and last 128. Canonical hostname is IDNA ASCII, matching the existing parser.
- 16-dimensional embeddings; three Conv1d branches, kernels 3/5/7, 24 channels
  each; ReLU/global max pooling; dense 72→32→1 with training dropout 0.2.
  AdamW, learning rate 0.001, weight decay 0.0001, eight epochs, batch 128,
  seed 42, deterministic CPU training with four threads. Official-navigation
  training rows have weight 3, matching the revised classical research policy.
- Best epoch **7**, selected only by selection-set balanced accuracy.
- Cascade candidate gates [0.3,0.7], [0.2,0.8], [0.1,0.9], CNN weights 0.5/1.0;
  selection-set balanced accuracy chooses the policy, with lower routed fraction
  breaking ties. Frozen policy: inclusive RF interval **[0.1,0.9]**, CNN weight
  **1.0** within the interval. Outside it the classical probability is unchanged.
- Threshold 0.5 fixed. Neither raw CNN nor cascade probability is calibrated.
- Weights, vocabulary, selected epoch and gate are saved before either evaluation
  CSV is opened. No tuning or replacement follows test outcomes.

## Evaluation evidence

A 2,000-record holdout was frozen before neural training from unused records in
the local original UCI archive: 1,000 benign and 1,000 phishing, one record per
registrable-domain skeleton. Original UCI labels are explicitly inverted.
All previous processed splits, observed UCI samples and separate Person 3
fixtures are excluded by domain skeleton. **21,291 previously used groups,
zero holdout overlap.** This is a balanced historical same-source test, not
newly collected attacks, population prevalence or temporal validation.

| Model | Fresh UCI accuracy | Recall | False-positive rate |
|---|---:|---:|---:|
| Classical v6 | 89.75% | 92.90% | 13.40% |
| CNN | 98.85% | 97.90% | 0.20% |
| Cascade | 98.60% | 97.60% | 0.40% |

The 1,698-row run06 final was previously inspected. Its new comparison is
**retrospective**, with only eight benign domains; it is not a fresh final set.

| Model | Run06 accuracy | Recall | False-positive rate |
|---|---:|---:|---:|
| Classical v6 | 90.81% | 90.00% | 5.79% |
| CNN | 93.99% | 97.88% | 22.26% |
| Cascade | 94.52% | 98.18% | 20.73% |

Cascade confusion matrices (rows actual benign/phishing; columns predicted
benign/phishing): fresh UCI `[[996,4],[24,976]]`; retrospective run06
`[[260,68],[25,1345]]`. Better aggregate accuracy does not erase the false alarms.
Source shift remains a material research limitation.

Post-freeze string stress tests use 200 paired samples per family from the
historical run06 final. Cascade variant recall: homoglyph 100%, deceptive
subdomain 100%, percent encoding 99.5%; zero losses among detections of the paired
originals. These are offline synthetic strings, not live verified malicious sites.

Known benign controls regress: PayPal/login gets 99, GitHub repository gets 100,
and example.com gets 100. W3C WCAG gets 10 and GitHub root 38. These are disclosed
failures, not candidates removed from the test. Do not demo the candidate as a
reliable replacement for the classical model.

Thirty warm CPU batch-one calls per control, excluding SHAP/HTTP:
GitHub root median 13.85 ms / p95 14.19 ms; example.com median 13.71 ms /
p95 13.98 ms. Both routed through the CNN; there is no measured speedup claim
against a matched baseline. Raw measured timing samples are in the evidence.

- [Full aggregate evaluation/stress/latency evidence](evidence/person1/neural-results.json)
- [Real model TestClient contract evidence](evidence/person1/neural-api.json)
- Artifact weights SHA256:
  `fc1ae95b2a94435268c0e4e3db454f745844aa59ac843984848e712bef79a4db`.
- Holdout CSV SHA256:
  `bfcd4a65613010ca407547d9cf15439eacd4666c06d8f77b0b9ef06e52022579`.

## Explicit provider contract for Person 2

`ml.neural_integration:create_provider` loads both frozen models once, validates
weights/parser/resource hashes and the classical-model checksum, and uses four
CPU threads. `Prediction.context` adds `model_used` (`classical` or `cascade`),
`cascade_status` (`available`), `cnn_routed` and `classical_probability`.
The API accepts these route fields while retaining classical defaults for the
existing provider. `/health.cascade_status` reflects the connected provider.
The frontend identifies a research cascade when connected.

For an unrouted output, the existing probability-scale RF SHAP remains valid.
For a CNN-routed output, explanation status is unavailable and items are empty;
RF reasons are never relabeled as an explanation of neural output. A validated
neural explanation method is future work. Neither this API seam nor TestClient
checks constitute browser acceptance or deployment validation.

## Reproduce

Install the existing recorded classical requirements, then:

```bash
.venv/bin/python -m pip install -r ml/requirements-neural.txt
export PYTHONPATH="ml:."
.venv/bin/python scripts/prepare_neural_holdout.py data/processed/neural-holdout01
.venv/bin/python scripts/train_neural.py data/processed/revised-run06 artifacts/neural-run01 artifacts/revised-run06/classical.joblib data/processed/neural-holdout01
.venv/bin/python scripts/report_neural.py artifacts/neural-run01 artifacts/revised-run06/classical.joblib data/processed/revised-run06 docs/evidence/person1/neural-results.json
```

Use a clean snapshot checkout or new outputs; scripts refuse existing outputs.
Holdout reproduction requires the exact exclusion inputs recorded in its
manifest. Later runs must exclude already inspected holdouts and create a new
version; do not reuse one as fresh evidence. Only PyTorch state dictionaries
are loaded, explicitly with `weights_only=True`, following the official
[PyTorch serialization guidance](https://docs.pytorch.org/docs/stable/notes/serialization).
Same-machine determinism is configured; different platforms/library builds may
still change results. Requirements record the installed PyTorch version.

For a deliberate **research-only** server, after extracting the private handoff:

```bash
export PYTHONPATH="ml:."
export PHISHX_MODE=model
export PHISHX_PROVIDER=ml.neural_integration:create_provider
export PHISHX_MODEL_PATH="$PWD/artifacts/revised-run06/classical.joblib"
export PHISHX_NEURAL_PATH="$PWD/artifacts/neural-run01"
export PHISHX_ALLOW_RESEARCH_CASCADE=1
.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

The ordinary `scripts/start-dev.sh` deliberately keeps serving classical v6.
Package with `PYTHONPATH=ml:. .venv/bin/python scripts/package_neural_handoff.py`.
The ignored `artifacts/handoff/PhishX_neural_research_v1.zip` contains weights,
metadata, policy, aggregate evaluation and file checksums. The existing classical
model ZIP is separately required. A second private archive,
`artifacts/handoff/PhishX_neural_snapshots_v1.zip`, contains the exact original
UCI archive, exclusion inputs, frozen holdout and per-file checksums for research
reproduction. Extract it into a clean checkout before the preparation command.
No raw datasets or model weights enter Git.

## Remaining project gates

A more representative external/temporal holdout and false-positive reduction
are required before promotion. Any next experiment must freeze new evaluation
data and retain this failed promotion result. Neural explanations, final browser
acceptance, verified container hosting and independent team review remain open;
these must not be marked complete by the existence of a trained checkpoint.

Verification: 77 Python tests and 11 subtests passed; frontend production build
passed; pip check found no broken requirements. No new browser screenshot or
Docker execution is claimed.
