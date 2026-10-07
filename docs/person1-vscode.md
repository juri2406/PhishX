> Current review model: run06, 24-feature extended profile. Receive the trusted
> [revised handoff](model-handoff.md), use the default **PhishX model backend**
> VS Code task, and follow [the revised workflow](person1-revised-workflow.md)
> for new-source training. The older UCI training commands below retain the
> 18-feature baseline for historical reproduction.

# Person 1 work in VS Code

Open the PhishX folder. Use Terminal > New Terminal for commands, and Terminal >
Run Task for the supplied tasks. The task labels are PhishX tests, analyze URL,
train model, and model backend. Run and Debug also includes a backend launch.
VS Code's Python and Python Debugger extensions are needed for interpreter,
test explorer, and debugger features. Terminal tasks work independently.

The local macOS interpreter is `.venv/bin/python`. On Windows, select
`.venv/Scripts/python.exe` with Python: Select Interpreter. The tasks contain
Windows command overrides. VS Code sets PYTHONPATH to the shared `ml` folder.
If you use an existing terminal, create a new terminal after opening the project
so it picks up that environment.

## Reproduce the research run

The initial source is UCI PhiUSIIL, donated 3 March 2024, licensed CC BY 4.0:
https://archive.ics.uci.edu/dataset/967/phiusil-phishing-url-dataset

Attribution: Prasad, A. and Chandra, S. (2024). PhiUSIIL Phishing URL (Website).
UCI Machine Learning Repository. https://doi.org/10.1016/j.cose.2023.103545
License: https://creativecommons.org/licenses/by/4.0/

Its labels are 1 legitimate and 0 phishing. The importer reverses them to match
PhishX. It ignores the dataset's precomputed features. Individual source
collection dates are unknown; import time is recorded separately. A balanced
5,000-per-class sample gives a manageable first run and does not reproduce
real-world prevalence. This initial source supplements the proposed feed-based
work. Fresh independently labeled sources remain necessary for external and
temporal evaluation.

From the VS Code terminal on macOS:

```sh
source .venv/bin/activate
export PYTHONPATH="$PWD/ml:$PWD"
curl -fL --max-time 600 'https://archive.ics.uci.edu/static/public/967/phiusiil%2Bphishing%2Burl%2Bdataset.zip' -o data/raw/phiusiil.zip
python scripts/import_uci.py data/raw/phiusiil.zip data/raw/uci_sample.csv --per-class 5000 --seed 42
phishx prepare data/raw/uci_sample.csv data/processed/uci-run02
phishx train data/processed/uci-run02 artifacts/uci-run03
phishx robustness data/processed/uci-run02 --model artifacts/uci-run03/classical.joblib --output artifacts/uci-run03-robustness --per-family 200
python scripts/import_uci.py data/raw/phiusiil.zip data/raw/uci_fresh_test.csv --per-class 2000 --seed 2026 --exclude-csv data/raw/uci_sample.csv
python -m scripts.evaluate_external artifacts/uci-run03/classical.joblib data/raw/uci_fresh_test.csv data/raw/uci_sample.csv artifacts/uci-run03/fresh-evaluation.json
python -m scripts.verify_model artifacts/uci-run03/classical.joblib data/raw/uci_fresh_test.csv artifacts/uci-run03/api-verification-fresh.json
python scripts/fresh_report.py artifacts/uci-run03 docs/evaluation-run03.md
python -m scripts.verify_model artifacts/uci-run03/classical.joblib data/processed/uci-run02/test.csv artifacts/uci-run03/api-verification.json
python -m pytest tests backend/tests -q
```

Use new input and output names for later runs. Scripts reject overwriting
existing datasets, split directories and model output directories. Keep the
archive and companion source manifest for exact reproduction.

For a fresh environment, install `python -m pip install -e .`, plus
`python -m pip install -r backend/requirements-dev.txt -r backend/requirements-model.txt`.
The local editable install may need explicit PYTHONPATH if Python ignores its
path file. VS Code tasks and pytest configuration already set the source path.
Do not copy the macOS virtual environment to Windows. Recreate it there.

## Files to review

- `ml/phishx/dataset.py`: cleaning, connected group splitting and checksum audit.
- `ml/phishx/model.py`: validation selection, held-out metrics and probability diagnostics.
- `ml/phishx/robustness.py`: offline synthetic manipulation tests.
- `ml/integration.py`: startup-loaded provider for the existing backend.
- `docs/evaluation-run03.md`: aggregate results once the run has completed.
- `artifacts/uci-run03/errors.json`: local false positives and false negatives.

## Run the trained backend

Choose Terminal > Run Task > PhishX model backend, or use the Run and Debug
configuration. This loads the experimental `artifacts/uci-run03/classical.joblib` in model mode. Known navigation paths can still produce false alarms; use it for local review.
The API serves http://127.0.0.1:8000/docs and does not use fixture responses.
The backend reports explanation availability honestly. Install SHAP and run the
SHAP checks before claiming explainability is complete.

## Review before calling the model ready

Inspect the source-bias diagnostics, false positives, false negatives and
probability bins. Confirm the source label mapping, dataset checksum and the
split hashes. Compare original versus altered URL recall without changing the
model after seeing test results. Any subsequent tuning needs a new independent
final evaluation set. A strong score on an old source does not establish
current-day phishing detection or full project completion.
