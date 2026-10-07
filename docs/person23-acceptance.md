# Person 2 revised-model acceptance - 7 October 2026

Person 2's remaining classical-path acceptance work against run06 is complete.
This supplements the historical run03 acceptance in person2-acceptance.md.
The API/frontend behavior is unchanged; the current model has 24 numeric
features and a separately measured external-source report. No model weights
or raw datasets are committed.

## Application and model integration

The separate Person 3 fixture ran 20 times through the built React UI and Vite
proxy, with 16 probability/normalized-host/SHAP parity checks and four visible
validation errors. A separate live HTTP report reproduces those checks through
scripts/review_fixture.py. The model version is rf-v6-d5923fe7d93e-20261007;
classical path, no cascade, unavailable live signals and uncalibrated wording
remain explicit. No scores or explanations were overridden.

Keyboard submission/result focus, visible 3 px submit focus, blank-submit
prevention, disabled controls during loading, 390/320 px mobile layouts and
real API-offline/retry recovery passed. The loading test used a temporary
1500 ms wrapper, then the ordinary API was restored. Screenshots and state
observations are linked from person3-review.md. The evaluation footer resolves
to the measured run06 report. No frontend redesign or second URL parser was added.

## Fresh checkout

A git archive of commit 50c800c was extracted into a new temporary directory.
A new Python 3.14 environment installed backend development requirements,
pinned ML packages and the editable repository package. No existing virtual
environment or raw dataset was copied. The trusted run06 model was copied via
its checksum-protected handoff.

- Fresh test suite: 51 passed, 11 subtests, no skips.
- Fresh pip check: no broken requirements.
- Fresh frontend: 78 packages installed from pnpm-lock.yaml; build passed.
- Fresh factory startup: 10 live HTTP model/SHAP/error cases passed.
- One non-failing Starlette/httpx deprecation warning remains.

The fresh check used macOS arm64. Windows launch instructions and checksum
selection are retained; a new Windows machine was not simulated or claimed.
Evidence: evidence/person3/fresh-environment.json and fresh-http.json.

## Measured ordinary API latency

Thirty undelayed localhost scans of https://github.com/ gave medians:

| Measurement | Median |
|---|---:|
| Local HTTP request | 28.831 ms |
| Inference including shared extraction | 13.712 ms |
| SHAP explanation | 14.382 ms |
| Backend total | 28.006 ms |

The API was already exercised. Separate medians need not sum exactly. These
are local development timings, not cold startup, deployment or load results.
Raw timings: evidence/person3/model-latency.json.

## Remaining scope

No remaining implementation task was identified for Person 2's local classical
milestone. Person 3's separate fixture/materials are supplied with clear
assistant authorship. Three fixture label disagreements and the known GitHub
false alarm remain model research limitations owned by Person 1; they are not
hidden by application pass counts. Later cascade integration, live network
signals, hosting and deployed validation are the planned remaining 40%.
