> Updated final review: [person3-user-guide.pdf](person3-user-guide.pdf). Person 2 run06 checks and Person 3 technical review materials are supplied; older pending statements below retain historical context. Human teammate sign-off is not claimed.

# Revised model note — 7 October 2026

The default VS Code/model PowerShell launcher now selects run06. Receive
`PhishX_model_handoff_v6.zip` and follow [the current handoff](model-handoff.md).
The browser acceptance cases/screenshots below were recorded with run03 and
remain evidence for that version. Current model API/SHAP/latency checks are
in `evidence/person1/`; review [run06](evaluation-run06.md) for current metrics
and known errors. To reproduce the old demo use `-ModelRun uci-run03` or set
`PHISHX_MODEL_PATH` explicitly to the old artifact.

# Running the real-model demo

Open the repository folder in VS Code. Follow [the model handoff](model-handoff.md)
to obtain the trusted artifact and verify its checksum. A Git clone alone does
not contain the trained model.

## macOS / Linux

From the repository root, create a Python environment and install dependencies:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt -r ml/requirements-verified.txt -e .
```

Select **Terminal → Run Task → PhishX model backend** in VS Code. Alternatively:

```sh
export PYTHONPATH="$PWD/ml:$PWD"
export PHISHX_MODE=model
export PHISHX_PROVIDER=ml.integration:create_provider
export PHISHX_MODEL_PATH="$PWD/artifacts/uci-run03/classical.joblib"
.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```sh
cd frontend
pnpm install --frozen-lockfile
pnpm build
pnpm preview --port 5173 --strictPort
```

## Windows

Use the Windows environment commands in the [README](../README.md). Install the
pinned ML requirements as well as backend dependencies and the repository
package. Start the checksum-verifying model launcher:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-model.ps1
powershell -ExecutionPolicy Bypass -File scripts/start-ui.ps1 -Preview
```

Build the frontend first. These Windows launchers were supplied and verified by
Person 2 on Windows; the additional fresh-copy check here was on macOS.

## Demonstration

Open `http://127.0.0.1:5173`. Wait for **Model API ready**. Choose **Official
domain**, then **Analyze URL**; the frozen model gives GitHub root 16/100. Choose
**Synthetic lookalike** and analyze again; it gives 96/100 with a PayPal match.
These are measured URL-text controls, not guaranteed safety or live-page labels.
Try **Synthetic subdomain** for structural signals. Enter `https://x..com` to
demonstrate validation, then submit a valid example to demonstrate recovery.

Inspect the separate **Model contributions** and **Observed signals** sections.
Open **API response** for the actual model version and output. The evaluation
link contains measured historical-source results and known false alarms. Live
domain checks and the cascade remain explicitly unavailable.

If the API is unreachable, restart it and choose **Retry connection**. If the
model is not ready, verify the artifact, dependencies, and provider settings.
Do not substitute fixture scores for this demonstration.

From the repository root, verify real HTTP output against standalone inference:

```sh
PYTHONPATH=ml:. .venv/bin/python scripts/verify_application.py
.venv/bin/python scripts/measure_latency.py --url https://github.com/ --runs 30
```

Use `--test-csv data/raw/uci_fresh_test.csv` to reproduce the 20-case historical
acceptance pass when that ignored source file is available. Windows uses
`.venv\Scripts\python.exe` and `$env:PYTHONPATH="$PWD\ml;$PWD"` instead.

The model is experimental and uncalibrated. App acceptance does not complete
Person 1's remaining research or replace Person 3's independent review.
