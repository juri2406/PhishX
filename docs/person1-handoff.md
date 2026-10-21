# Person 1 → Person 2 handoff

**Current default:** release v7; see the current contract below and
`project-completion.md`. The older sections describe classical milestone history.


## Revised frozen classical model — 7 October 2026

The new local review model is `artifacts/revised-run06/classical.joblib`, version
`rf-v6-d5923fe7d93e-20261007`, SHA256
`a5a68744712975f0f5809dd6f13825eeb47dc4251153f3f65eadc2120727d3ed`.
Its `extended-v1` profile has 24 numeric features: the original ordered 18 plus
`host_digit_count`, `path_digit_fraction`, `path_segment_count`, `path_entropy`,
`government_suffix`, and `known_brand_domain`. It calls the same base parser
and extractor, then adds signals; no legitimate-domain verdict override exists.
The bundle also requires the extended extractor hash. Missing, stale, reordered
or unknown profiles are rejected. Older 18-feature bundles remain supported.

Labels remain 0 benign / 1 phishing. The 150-tree forest returns raw class-1
probability, `calibrated=false`. Sigmoid/isotonic were fitted/reviewed separately
but are not served. Provider and SHAP use the bundle's ordered feature schema
and store the exact row in Prediction.context. Class 1, probability-scale SHAP
and additivity passed on 20 final URLs. API fields and risk bands are unchanged.

See [run06 evaluation](evaluation-run06.md) and
[the reproduction workflow](person1-revised-workflow.md). The final 1,698-row
external-source sample measured 90.81% accuracy, 90% recall and 5.79% FPR.
The GitHub repository control still scores 55 and remains a known false positive.
This experimental model does not establish deployment calibration or universal
detection. Person 3's separate fixture/review materials are supplied in person3-review.md; no human sign-off is claimed.

The historical run03 instructions below remain valid for the earlier artifact;
use the revised model handoff instructions for run06.


No input from Person 1 is needed to run fixture mode. The real integration needs:

| Item | Required details |
|---|---|
| Frozen artifact | Local location, checksum, version, estimator/library versions |
| Shared parser | Callable used in training and inference; normalization rules |
| Features | Ordered names, numeric types, missing-value handling, transformed representation |
| Labels | Binary classes and explicit phishing label/index |
| Probability | predict_proba extraction and calibration status |
| Brands | Legitimate-domain exclusions, skeleton version, distance definition |
| SHAP | Estimator compatibility, explicit output class and scale, additivity output function |
| Evaluation | Real held-out report and manipulation-family counts/results |

The 2048-character request limit and HTTP/HTTPS schemes are proposals for review.
No feature names are fixed by this application; the extractor's frozen schema wins.

## Provider factory contract

Implement a trusted local factory configured as `module:create_provider`.
The app imports and calls it once in lifespan. It returns an object with:

```python
version: str
calibrated: bool
predict(url: str) -> backend.app.providers.Prediction
explain(prediction: Prediction) -> backend.app.providers.AttributionResult
```

`predict` calls the shared parser, feature extractor, skeleton matcher and model.
Raise `backend.app.providers.InvalidURL` for malformed input. Return the actual
normalized host, phishing-class probability, observed signals, optional brand
and normalized skeleton distance. Store the exact ordered model row in
`Prediction.context` for explain; never recompute features differently.

`explain` returns verified SHAP contributions to the phishing output. Initialize
the explainer in the factory, not on every request. Shared objects must support
concurrent requests; keep request feature rows in the Prediction, not mutable
provider state. Call `backend.app.shap_adapter.TreeShapAdapter` if compatible.

The helper supports binary tree estimators with classes_ and numeric features.
Pipelines need their exact transformation applied first and the estimator's
post-transformation schema. For single-output SHAP arrays, pass the explicit
`single_output_label` only after confirming that output belongs to phishing.
If it corresponds to the other class, supply an appropriate reviewed adapter;
do not silently flip or guess. `output_fn(row)` must compute the model output
on the declared scale for the phishing class. Its result is checked against
SHAP base + contributions on every explained row. TreeExplainer's default raw
output can be probability for some estimators and a margin for others; naming
the scale does not change it. Confirm it with the model owner.

No calibration is implied by SHAP additivity. Additivity is necessary but cannot
by itself prove semantic label correctness; the class mapping must be reviewed.

Acceptance: run genuine benign, phishing and Unicode samples through the shared
parser; verify feature order, predicted phishing-class probability, SHAP class,
scale and additivity. Check explanation failures and malformed input. Rerun
latency measurements in model mode. Preserve results with model version.

## Initial Person 1 package

Install the repository package with `python -m pip install -e .`.
The shared parser is `phishx.normalize_url` and extraction is
`phishx.analyze_url`. `FEATURE_NAMES` defines 18 numeric features in order.
No missing values are produced: unavailable live signals are excluded from the
model. The starter estimator is a random forest, selected on validation F1.
Class 0 is benign and class 1 is phishing, with the class index read explicitly.
Probability remains uncalibrated. Unicode mapping version is 16.0.0 and brand
resources carry checksums in the exported bundle. The parser permits bare
hostnames for CLI/data import, while the existing HTTP API requires a scheme.

Use `PHISHX_PROVIDER=ml.integration:create_provider` and set `PHISHX_MODEL_PATH`
to a trusted local `classical.joblib` file. The factory validates schema and
resource hashes, loads the estimator once, and returns the exact feature row in
Prediction.context. It attempts the existing TreeShapAdapter with probability
scale and phishing label 1. If SHAP initialization fails, prediction still works
and explanations explicitly fail as unavailable through the backend contract.
An experimental real-data artifact and fresh evaluation are now available. See evaluation-run03.md for results and remaining false alarms.

## Extractor version checks

New artifacts include hashes of features.py, urls.py and skeleton.py in addition
to brand/Unicode resource hashes. An old artifact without the extractor version
is rejected by the current inference code. Retrain rather than bypassing the
check. The current feature representation uses the canonical URL, treats absent
root paths as `/`, and removes one leading `www` presentation prefix for lexical
ML features. It preserves the submitted/actual hostname in the report. Raw
encoding indicators remain separate features. Feature count/order is unchanged.


## Experimental artifact from the VS Code work

Local artifact: `artifacts/uci-run03/classical.joblib`.
Version: `rf-v2-1774537c789e-seed42`.
SHA256: `2b59557ed0a23220bd69e0f2775ad934d20fa1587ff71fe2decb750fb2ff8ac7`.

The model uses 18 numeric features, 150 random-forest trees, max depth selected
on validation F1, label 1 for phishing, and uncalibrated probability output.
The existing TreeShapAdapter passed phishing-class, probability-scale and
additivity checks through FastAPI on 20 fresh held-out URLs. Do not calibrate
or change preprocessing without revisiting this explanation contract.

Fresh evaluation: 4,000 UCI records from domain/skeleton groups excluded from
the entire initial 10,000-row sample. Accuracy 95.25%, phishing recall 92.55%,
precision 97.83%, false-positive rate 2.05%. These are same-source historical
results, not temporal or external-source validation. The artifact still flags
some known official-domain navigation paths and remains experimental.

Run the VS Code task `PhishX model backend` for local review. Use the committed
reproduction guide to rebuild the model on a teammate's machine. Binaries and
raw records remain outside Git. The aggregate report records source attribution,
checksums, synthetic-family counts and known failures.

See [receiving the model](model-handoff.md) for the prepared ZIP contents,
checksum verification, destination path, and VS Code startup steps.

## Supplied model handoff on this checkout

Person 1's PhishX_model_handoff.zip supplies the trusted experimental model at
`artifacts/uci-run03/classical.joblib`, version `rf-v2-1774537c789e-seed42`.
Its verified SHA256 is
`2b59557ed0a23220bd69e0f2775ad934d20fa1587ff71fe2decb750fb2ff8ac7`.
The file stays ignored by Git; another checkout still needs its own handoff copy.

Install the package with `.\.venv\Scripts\python.exe -m pip install -e .` and
the optional SHAP dependencies from backend/requirements-model.txt. From the
repository root, launch the real backend with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-model.ps1 -ModelRun uci-run03
```

Stop any existing backend on port 8000 first. This launcher verifies the handed
off checksum and sets PHISHX_MODE, PHISHX_PROVIDER and PHISHX_MODEL_PATH; it does
not fall back to fixture predictions. Use `-Port 8001` for a separate API check;
the frontend's default local proxy still targets port 8000.
The model is experimental and uncalibrated; known legitimate navigation paths
can produce false alarms. See docs/evaluation-run03.md. Local smoke checks verify
integration and explanations, not new held-out accuracy or milestone completion.


### Windows compatibility

The frozen artifact hashes exact extractor/resource bytes. `.gitattributes`
preserves their original LF line endings. CRLF-only checkout differences were
restored to the model's expected SHA256 values without changing ML code.
Do not remove or bypass the model compatibility checks.
For the full Unicode test suite on Windows, run:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest tests backend/tests -q
```

This avoids Windows legacy default encoding in a Person 1 CSV test.

Parser errors keep HTTP 422 and `INVALID_URL`. The main message gives hostname/encoding recovery instructions; `error.details` retains the original parser reason under field `url`.


## Person 2 next stage (21 October 2026)

Optional live observations now use a separate `POST /signals` endpoint. Enable
with `PHISHX_LIVE_SIGNALS=1` in model mode, or run
`bash scripts/start-dev.sh --live` on macOS. `/health` adds
`live_signals_enabled`. The existing `/scan` response and frozen model remain
unchanged; its `unavailable_signals` describes the text-only model response,
while separately requested observations appear in the live-check panel.
DNS/TLS/HEAD redirects/RDAP have explicit failure states and never change scores
or SHAP explanations. Fixture mode cannot perform network checks.
See [next-stage status](person2-next-stage.md) for measured verification
and remaining gates; [container candidate](../deploy/README.md) is unbuilt here.
CNN integration, new browser acceptance and verified hosting remain open.


## Person 1 neural research handoff (21 October 2026)

The character CNN and uncertainty cascade are trained and evaluated. See
[the neural handoff](person1-neural-handoff.md) for frozen artifacts, source
limitations, commands and measured regressions. The new cascade is **not promoted**:
its false-positive rate on the retrospective broader-source run06 set rises
from 5.79% to 20.73%, despite stronger recall and a good fresh historical UCI result.
Classical v6 remains the default and the ordinary launcher is unchanged.

Explicit research factory: `ml.neural_integration:create_provider`, requiring
`PHISHX_ALLOW_RESEARCH_CASCADE=1` and `PHISHX_NEURAL_PATH`. `/scan.model_used`
now permits `classical` or `cascade`; `cascade_status` permits `not_implemented`
or `available`. Route metadata comes from the frozen provider, never from UI
fixtures. `/health` reflects the connected provider. Neural-routed predictions
have unavailable explanations; RF SHAP is supplied only for unchanged RF output.
No neural SHAP or calibrated probability is claimed. Raw holdouts and weights
remain ignored and are handed over privately. Final neural-quality promotion,
browser acceptance and deployment are still open.


## Person 3 final-stage review (21 October 2026)

A new independent 20-case fixture has now been reviewed through both real model
APIs and both browser interfaces, with six new screenshots and an updated
one-page guide. Application parity passed 20/20 per model; the classical model
had one benign false positive and two source-labelled misses. The tiny cascade
fixture does not establish promotion or general accuracy. See
[the final-stage review](person3-final-review.md) for provenance, defects,
live-check/outage observations and remaining project gates. Review was performed
by Codex; no human teammate signature or approval is claimed.


## Earlier completion work (historical)

The completion branch adds optional `explanation_method` and `explanation_audit`
fields. A release provider can compute exact four-component Shapley values
(protocol, authority, path, query) by evaluating all 16 coalitions of the entire
frozen cascade; the stated reference is never fetched, and fragments remain
constant. The signed contributions plus baseline must reproduce the actual
model output within 1e-5. This is distinct from classical numeric-feature
TreeSHAP. No explanation is fabricated when validation fails.
Health adds `model_profile` and `model_notice` for truthful provider identification.
Failed candidates remain blocked by their recorded promotion gates. See
`docs/evidence/completion` for the failed experiments; the current v7 selection and verification supersede this earlier status.


## Release v7 integration contract

Both Docker and `scripts/start_dev.py` now select `ml.completion_integration:create_provider`,
`PHISHX_RELEASE_PATH=artifacts/release-v7` and its classical weight file. The private
handoff contains the RF, CNN, learned fusion, frozen ranking context, metadata,
policy and passing evaluation report. The factory recomputes registered gates
from measured confusion counts and verifies model/feature hashes before use.
Health reports `model_profile=release_cascade`. Scan responses retain existing
fields and add optional `explanation_method` and `explanation_audit`; v7 uses
`exact_url_component_shapley` across the full prediction pipeline, with explicit
reference URL, baseline, signed protocol/host/path/query contributions and residual.
Observed popularity rank is learned frozen context, not a benign override. Labels
and risk bands remain unchanged. See the current report for sampled results and
historical-label/ranking timing limits. Earlier candidate failures remain recorded.

Human acceptance is pending the user report in `human-acceptance.md`.
