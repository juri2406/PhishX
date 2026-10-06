# PhishX: Person 2 implementation

This checkout implements the application work that can proceed independently of
Persons 1 and 3. Stack: FastAPI, React, Vite and Tailwind. Nothing here trains a
phishing classifier, implements a second URL feature parser, or claims the 60%
milestone is complete. The PDF was used as a task reference, not as authorization
to publish, send messages, or change teammates' modules.

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

Pending Person 1: shared parser, real feature schema and skeleton matching,
frozen trained artifact, class mapping, calibration status, evaluation data and
verified SHAP compatibility. No `ml/` or training code has been created.
Pending Person 3: independently labeled fixture, manual results and screenshots.
Their delay does not block this development demo.

## Connect the real model later

See `docs/person1-handoff.md`. The provider factory loads exactly once at API
startup. It owns loading the artifact and using Person 1's shared parser. Restart
the API after changing artifacts/configuration. The backend never downloads a
model or deserializes arbitrary uploaded files.

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-model.txt
$env:PHISHX_MODE = "model"
$env:PHISHX_PROVIDER = "ml.integration:create_provider"  # Person 1 supplies this
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

`PHISHX_MODE` defaults to `model`. Without a usable factory, `/health` reports
`ready=false` and `/scan` returns 503. There is no automatic fixture fallback.
The example module path above is a proposed handoff, not an existing module.
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
