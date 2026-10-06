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
