# CNN extension verification - 21 October 2026

Source: local C:/Users/MEGHA/PhishX checkout copied into this chat's workspace.
The original checkout was not edited. Remote GitHub access returned 404.

Implemented: training-only vocabulary, character CNN, validation checkpoint
selection, RF-first lazy cascade, validation threshold selection, frozen
model comparison, local validation/final error exports, latency and provenance.
The existing web application continues to use its classical path until Person 2
integrates the new adapter.

## Actual checks

- Full ML and backend regression suite: **59 passed, 11 subtests passed**,
  with one pre-existing Starlette/httpx deprecation warning; 75.96 seconds.
- Eight new CNN tests passed within that suite, including a two-epoch synthetic
  training/checkpoint/reload/cascade/evaluation round trip. Synthetic fixture
  predictions are engineering checks, not detection-quality measurements.
- The training test rejects any attempt to open test.csv, then separately
  runs frozen evaluation. Other tests cover unknown characters, head/tail
  truncation, padding invariance, gradients, lazy escalation, gate constraints,
  split tampering/leakage, output overwrite rejection and artifact tampering.
- New workflow CLI help executed successfully.
- PyTorch CPU 2.14.1+cpu installed into workspace-only dependencies for checks;
  existing checkout Python 3.13 and its ML/backend dependencies were reused.
- Windows tests require writable workspace TEMP/TMP and UTF-8 mode for an
  existing research test that otherwise uses the Windows default encoding.
  Initial temporary-folder/encoding failures were resolved by the test
  environment; no legacy test behavior was changed to hide a defect.
- Frontend dependency installation was attempted in both the copied frontend
  and a scratch copy. pnpm could not create required Windows symlinks (EPERM),
  so the frontend build could not be verified here. Frontend source is unchanged.

Equivalent regression invocation after installing project/backend dependencies:

```powershell
$env:PYTHONUTF8 = '1'
$env:TEMP = Join-Path (Get-Location) 'work/tmp'
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
python -m pytest tests backend/tests --basetemp=work/pytest-cnn -q
```

## Not yet measured

No real-data CNN training, cascade accuracy improvement, new robustness
result or production latency is claimed. This checkout lacks the run06 RF
artifact and its exact prepared datasets. The existing run03 artifact is
insufficient to reproduce run06. Matching train/validation/test files and
manifest, a trusted matching RF, and agreed acceptance targets are needed.
Existing evaluated test sets must be reported as previously evaluated.

## Applying the delivery

PhishX_Person1_CNN.zip is a **changed-files overlay**, not a full repository
or a trained-model handoff. Review the files against the current branch before
copying them over; README, pyproject.toml, .gitignore and person1-handoff.md
include changes to existing files. New files are the three ML modules,
tests/test_cnn.py and the two CNN guides. No data, weights, dependencies,
secrets or generated model scores are included. The source checkout has not
been committed or pushed by this work.
