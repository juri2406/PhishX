# PhishX: classical phishing scanner

The shared Person 1 detection package and Person 2 application are integrated:
FastAPI, React, Vite, Tailwind, the frozen classical model, and verified SHAP
explanations. Person 2's local milestone acceptance is complete; the overall
60% milestone is not claimed because Person 3’s independent review
remains outstanding. Person 1’s classical research deliverables are complete
with explicit experimental-model limitations.

Start with the [real-model demo guide](docs/person2-demo-guide.md) and the
[Person 2 acceptance report](docs/person2-acceptance.md). Model binaries are
supplied separately through the trusted handoff.


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

See [run06 evaluation](docs/evaluation-run06.md) and
[the reproduction workflow](docs/person1-revised-workflow.md). The final 1,698-row
external-source sample measured 90.81% accuracy, 90% recall and 5.79% FPR.
The GitHub repository control still scores 55 and remains a known false positive.
This experimental model does not establish deployment calibration or universal
detection. Person 3's independent acceptance remains pending.

The historical run03 instructions below remain valid for the earlier artifact;
use the revised model handoff instructions for run06.

## Run the demo on Windows

Prerequisites: Python 3.11+ and Node 22.12+ with npm (or pnpm).
From PowerShell in the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
$env:PHISHX_MODE = "fixture"
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open a second PowerShell terminal:

```powershell
cd frontend
npm install
npm run dev
```

If using pnpm instead, run `pnpm install --frozen-lockfile` then `pnpm dev`.
The verified frontend lockfile is `frontend/pnpm-lock.yaml`.
Open http://127.0.0.1:5173. Pick one of the four fixture examples, then press
**Analyze URL**. API docs are at http://127.0.0.1:8000/docs.
The Vite dev proxy forwards `/api` to port 8000; no browser CORS override is needed.

Fixture mode is opt-in and serves exact sample URLs only. Its scores, brand match,
and observed signal are illustrative UI data, not detection evidence. Arbitrary
URLs return a structured 422 response. Samples use reserved example domains and
are never visited. There is no fabricated SHAP explanation.

## Convenient launch after setup

In two separate PowerShell terminals at the project root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-api.ps1 -Mode fixture
powershell -ExecutionPolicy Bypass -File scripts/start-ui.ps1
```

To serve the verified built frontend instead, use `scripts/start-ui.ps1 -Preview`.
This preview uses Vite's local API proxy and is for local review only.

## Current scope

Implemented independently:
- `/health`, `/scan`, strict request envelope validation, structured errors,
  response schema, score bands and per-request inference/explanation timing.
- Responsive scanner with loading, empty, error and result states; separate
  observed signals and model contributions, brand comparison and model details.
- Startup-loaded provider seam and optional binary tree SHAP adapter with
  class, feature-order, finite-value and additivity checks.
- API tests, synthetic SHAP unit checks, latency recorder and handoff templates.

Person 1's parser, features, skeleton matching, trained artifact and SHAP
compatibility are supplied. The revised model adds broader source coverage, a separate calibration review
and untouched final evaluation. Representative coverage and known false alarms
remain research limitations; see the run06 report.
Person 3's independently sourced fixture/review remains separate from the
recorded Person 2 developer acceptance pass.

## Run the real model

See `docs/person1-handoff.md`. The provider factory loads exactly once at API
startup. It owns loading the artifact and using Person 1's shared parser. Restart
the API after changing artifacts/configuration. The backend never downloads a
model or deserializes arbitrary uploaded files.

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-model.txt
$env:PHISHX_MODE = "model"
$env:PHISHX_PROVIDER = "ml.integration:create_provider"  # Existing shared provider
$env:PHISHX_MODEL_PATH = "$PWD\artifacts\revised-run06\classical.joblib"
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

`PHISHX_MODE` defaults to `model`. Without a usable factory, `/health` reports
`ready=false` and `/scan` returns 503. There is no automatic fixture fallback.
The provider module above exists and uses the shared Person 1 extractor.
Do not set fixture mode when collecting model/evaluation evidence.

## Contract (proposed for Person 1 review)

`POST /scan` body: `{"url":"https://example.com/"}`. HTTP/HTTPS only,
maximum 2048 characters, no whitespace/control characters, no extra fields.
Envelope checks are not the full URL parser: Person 1's shared parser handles
host syntax, Unicode/IDNA, credentials/ports, percent encoding, normalization
and malformed URL rejection in model mode. Its errors must map to `InvalidURL`.
Fixtures are exact string matches and do not normalize arbitrary input.

Response: `submitted_url`, `normalized_host`, `phishing_probability`,
`risk_score`, `risk_level`, `matched_brand`, `skeleton_distance`,
`observed_signals`, `explanation_items`, `model_used`, `cascade_status`,
`model_version`, plus mode, explanation availability/scale, calibration flag,
unavailable live signals and timings. `/docs` exposes the exact OpenAPI schema.
`skeleton_distance` is normalized 0–1 (0 is identical); null means unavailable.

`risk_score = round(100 * phishing_probability)` using Python round (ties to even).
Bands: Low 0–30, Medium 31–60, High 61–80, Critical 81–100.
Uncalibrated output is labeled a model score. Observed indicator points are
never added to the probability. Model path is `classical`; cascade is always
`not_implemented`. Domain age, DNS, TLS validity and redirects are unavailable.

Explanation status is `fixture`, `available` or `unavailable`. A successful
explanation with zero positive features has an empty list, not invented reasons.
Each explanation includes feature, observed value, positive contribution and
plain-language reason. At most three are shown, sorted by positive contribution.
Contribution units come from `explanation_scale`, not necessarily probability.
An explanation failure preserves the prediction but explicitly reports failure.

Errors are `{"error":{"code":"...","message":"...","details":[]}}`:
422 INVALID_REQUEST / INVALID_URL, 503 MODEL_NOT_READY, 500 INFERENCE_FAILED /
INVALID_MODEL_RESPONSE. Internal stack traces are confined to backend logs.
Submitted URLs are not included in application log messages. Keep this local
prototype bound to loopback; production security and deployment are later work.

## Verify and measure

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
cd frontend
npm run build
```

`test_shap_adapter.py` skips when optional model dependencies are absent.
It uses a tiny synthetic tree solely to test explanation mechanics; it is not a
PhishX model or an evaluation result.

With the API running, from the repository root:

```powershell
.\.venv\Scripts\python.exe scripts/measure_latency.py --runs 10 --output work/latency.json
```

The script records actual request and backend inference/explanation timings and
labels the mode/version. Fixture measurements must not be used as model latency.
Review `docs/person3-test-template.csv` and `docs/manual-checks.md` for the manual
handoff. `docs/implementation-status.md` records validation performed here.

For a separately hosted frontend, set `VITE_API_BASE` at build time to the backend
URL and explicitly configure allowed origins in the backend. A Vite production
build does not carry the development proxy; hosting remains outside this task.

Implementation references: [FastAPI lifespan testing](https://fastapi.tiangolo.com/advanced/testing-events/) and [SHAP TreeExplainer](https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html).

To reproduce the exact verified Python environment, install `backend/requirements-verified.txt` in a fresh virtual environment. It includes optional SHAP dependencies.

## Person 1 implementation

The shared detection package now lives in `ml/phishx/`. See
[Person 1 setup](docs/person1-setup.md) for installation, dataset preparation,
training and CLI commands, and [progress](docs/person1_progress.md) for remaining
real-data and robustness work. The shared parser uses the agreed 2048-character
limit. Raw datasets and model outputs stay outside Git.

## Earlier UCI evaluation (historical)

VS Code tasks and a backend debug configuration are available in `.vscode/`.
Follow [the VS Code guide](docs/person1-vscode.md) to reproduce the UCI import,
training and evaluation. The source is a historical CC BY 4.0 dataset, not a
current live feed. Its labels are inverted explicitly during import.

The first source-only model exposed severe formatting bias on ordinary URLs.
Its report is retained in `docs/evaluation-run02.md` as an experimental baseline.
The corrected extractor uses a consistent root path and removes the leading
`www` presentation prefix from ML features, while preserving the actual host in
reports. Frozen artifacts now contain extractor checksums and cannot silently
run against changed feature code. Real model outputs remain uncalibrated.

The corrected baseline and its fresh 4,000-record evaluation are documented in
[the current report](docs/evaluation-run03.md). Accuracy is 95.25% on that historical
source. Known navigation-path false alarms remain; the model is experimental.
VS Code's model-backend task points to the corrected local artifact in
`artifacts/uci-run03/`. Data and weights are not committed.

For the prepared model ZIP, file placement, checksum, and teammate setup, follow
[the model handoff instructions](docs/model-handoff.md). The ZIP is transferred
separately; cloning the repository does not include the model.

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
