# Local Docker demo and remaining model work

The local application uses the existing classical RF v6 model, real TreeSHAP,
shared URL parsing, Unicode skeleton/brand comparison, and optional DNS, TLS,
redirect and RDAP checks. Live checks require an explicit button click and do not
change the text model's score. Scores are uncalibrated model outputs, not the
probability that a website is safe. The application does not read target page bodies.

## Run on this Mac

From the repository root run `bash scripts/demo.sh`, then open
http://127.0.0.1:8080. Use `bash scripts/demo.sh status`, `logs`, or `stop` to manage
it. Docker Desktop or Docker/Colima and Compose must be installed. The script uses
a dedicated `phishx` Colima VM when needed. The backend is internal to Compose;
only localhost port 8080 is published. A trusted private model handoff must be at
`artifacts/revised-run06/classical.joblib`; model binaries and raw data stay out of Git.

## Research work implemented, not released

RF/CharCNN integration, learned fusion, popularity context and exact four-component
URL Shapley explanations are implemented separately. The release factory refuses
candidates whose frozen quality checks fail. None of the completion candidates
passed every gate, so the Docker demo retains the classical provider. This is an
academic prototype, and the entire model-quality objective is still incomplete.

Measured external cohort results at classification threshold 0.5:

| Candidate | Benign / phishing rows | Phishing recall | False-positive rate |
| --- | --- | --- | --- |
| 02 | 148 / 200 | 84.0% | 8.78% |
| v3 | 178 / 200 | 98.5% | 16.29% |
| v4 | 166 / 200 | 92.5% | 6.02% |
| v5 | 157 / 200 | 99.0% | 47.77% |
| v6 | 153 / 200 | 97.0% | 5.23% |

The predeclared external false-positive gate is at most 5%, with no worsening
against the RF baseline. v6 produced 8 false positives and 6 false negatives;
the baseline produced 7 and 34 on that cohort. Its separate balanced historical
UCI sample had 13 false positives and 7 false negatives among 2,000 rows.
These are convenience cohorts, not population or future-web accuracy estimates.
Later candidates reused earlier inspected cohorts as development data; fresh
candidate holdouts excluded all previously observed domain skeletons. The repeated
research revisions are disclosed and are not independent confirmations.

v6 uses frozen Tranco Top 1M list 262W9 acquired on 2026-10-21 as a learned feature,
not a whitelist or ownership guarantee. This context postdates the historical
phishing labels, so the experiment does not establish forward temporal validity.
The rank list and model weights are private local artifacts. Source:
https://tranco-list.eu/. Historical PhishTank labels are not current page checks.

The experimental explanation computes the exact Shapley values of protocol, host,
path and query across 16 URL combinations, with fragment held constant. Its
reference `http://a.b` is a placeholder, not a benign example. It explains the
model's output relative to that reference, not website safety or causal effects.
The default Docker model continues using feature-level TreeSHAP.

## Remaining acceptance work

Improve generalization using a broader independently labeled benign corpus and
new untouched evaluation cohorts. Do not tune thresholds on the failed final
cohorts or relax the gates to label them a success. Validate and promote a frozen
candidate only after all gates pass, then repeat Docker and browser checks for
that exact candidate. A human teammate's final acceptance has not been recorded.
Remote CI and GitHub publication must be verified separately from local checks.

## Verified local execution

On 2026-10-21 the Linux backend and nginx frontend containers built and ran on
this Mac using the dedicated Colima VM. Both run as nonroot users; the backend
root filesystem is read-only. Only `127.0.0.1:8080` is published.

Local checks: 83 Python tests plus 11 subtests passed; frontend production build
passed. Real HTTP checks verified standalone/deployed model and SHAP parity,
malformed input rejection, private live-target rejection, security headers and
blocked model/dotfile downloads. All four example.com live observations returned
available. These are point-in-time observations, not guaranteed future availability.
See `docs/evidence/completion/docker-http.json` for actual outputs and timings.
One smoke input, this project's legitimate GitHub URL, scored 55/100; do not
interpret model scores as verified labels or certified safety.

Browser checks verified the synthetic lookalike result, real model contributions,
focus moving to the result and the next Tab reaching live checks, and desktop/
390px mobile layout without horizontal overflow. Actual screenshots and the
review record are under `docs/evidence/completion/`. This is an agent review;
no human signature is implied. The private local model-only handoff is
`artifacts/handoff/PhishX_local_Docker_model.zip`, extracted at the repository root.
It must be shared separately from Git using a trusted channel.

The holdout manifests' legacy phrase "Frozen before neural training" should be
read as frozen before that candidate's fitting/evaluation: v5/v6 use an already
frozen v4 encoder. The manifests are preserved verbatim as evidence. Earlier
candidate code hashes refer to their source revision, not necessarily current
HEAD. Re-running old policies requires matching source and private artifacts;
never alter their recorded hashes to make an incompatible provider start.
