# Person 1 → Person 2 handoff

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
