> Updated final review: [person23-acceptance.md](person23-acceptance.md). Person 2 run06 checks and Person 3 technical review materials are supplied; older pending statements below retain historical context. Human teammate sign-off is not claimed.

# Person 2 acceptance — 7 October 2026

## Outcome and scope

Person 2's application tasks for the classical-path milestone are complete:
FastAPI, React scanner, real-model integration, SHAP explanations, validation,
startup instructions, developer acceptance checks, measured local latency and
a reviewable demo. This is not a claim that the full 60% project milestone or
the later cascade, live lookups and deployment are complete.

The frozen model remains experimental and uncalibrated. Person 1's data coverage,
false alarms, calibration review and independent evaluation remain separate
research work. Person 3's independent review was not manufactured or substituted
with the developer checks below.

## Real browser and HTTP evidence

The built React application was exercised through its actual Vite `/api` proxy
against a real Uvicorn server and the trusted Person 1 artifact. No fixture
provider or fabricated prediction was used. Submitted URLs were text only;
their pages were not visited.

The 20 browser cases comprised six historical UCI benign labels, six historical
UCI phishing labels, four explicitly synthetic homoglyph strings and four
malformed inputs. These are developer acceptance cases drawn from the existing
fresh held-out source, not an independent new accuracy benchmark. All 16 valid
browser probabilities, normalized hosts and SHAP contribution lists matched
standalone inference. Four invalid cases showed validation errors. Two UCI
labels disagreed with the model (one false positive and one false negative);
the application displayed the actual results, without overriding them.

The committed [browser summary](evidence/person2/acceptance-results.json) omits
raw dataset URLs. A separate [20-case HTTP parity run](evidence/person2/http-acceptance.json)
checks live responses against standalone predictions and SHAP. Reproduce it
with `scripts/verify_application.py`; use `--test-csv` when the ignored held-out
CSV is available. This verifies integration, not classification quality.

## State, keyboard and mobile checks

- Empty state and disabled blank-submit action work.
- Loading status appears and input, submit and example controls are disabled.
  This state was observed with a temporary 1.5-second middleware delay around
  the real provider. The delay was not shipped or used for latency results.
- Keyboard Enter submits; result focus moves to the result region. Tab focus
  on the submit button has the visible solid 3 px outline.
- No horizontal overflow at 390 px or 320 px; example controls are at least
  44 px tall. Long feature values and model versions wrap.
- Stopping the actual API shows the connection notice and a useful scan error.
  Restarting it, choosing Retry connection and scanning recovers successfully.
- Parser errors show a hostname/encoding recovery instruction; the original
  parser reason remains in structured API details. Subsequent valid scans work.
- Model examples are distinct from fixture examples. Synthetic strings are
  labeled synthetic. Uncalibrated wording, unavailable live signals and the
  unimplemented cascade remain explicit. The footer links the measured report.

See [state observations](evidence/person2/ui-state-checks.json). Console review
reported no browser runtime errors in the final check. This is a focused
functional/accessibility pass, not a full WCAG certification. Impeccable's
context/detector engine was unavailable; existing product/design context was
read directly and no automated detector success is claimed.

## Measured local latency

Thirty real HTTP scans of `https://github.com/`, after the provider had already
been exercised, gave these medians:

| Measurement | Median |
|---|---:|
| End-to-end localhost HTTP request | 30.303 ms |
| Backend inference | 13.643 ms |
| Backend SHAP explanation | 15.849 ms |
| Backend total | 29.434 ms |

SHAP added about 15.8 ms and represented about half the backend time for this
URL on this machine. The medians of separate stages need not sum exactly.
These measurements do not cover cold startup, deployed network latency,
concurrent load or all URL lengths. Raw measured timings are committed in
[model-latency.json](evidence/person2/model-latency.json). Reproduce with
`scripts/measure_latency.py --url https://github.com/ --runs 30`.

## Fresh setup and final checks

A source-only copy of commit `ae759aa`, with the final application changes
overlaid, was extracted into a new temporary directory. A new Python 3.14
virtual environment installed backend development dependencies, the pinned ML
requirements and the editable repository package. The trusted model was copied
through the handoff; raw data and pre-existing environments were not copied.

- Fresh Python environment: 47 tests passed, plus 11 subtests, with no skips.
- Fresh environment `pip check`: no broken requirements.
- Fresh frontend: installed from `pnpm-lock.yaml`; production build passed.
- Fresh-copy factory startup: real HTTP health/model scans passed.
- Final workspace tests and frontend build also passed.

One non-failing Starlette/httpx deprecation warning remains. The fresh build
check used macOS; prior Windows launcher verification is recorded in the
implementation history. See [the demo guide](person2-demo-guide.md) for startup
and verification commands. Another checkout still needs the trusted model ZIP.

## Screenshots and review material

Six actual captures accompany the developer pass:

- [Desktop empty state](evidence/person2/desktop-empty.jpg)
- [Official-domain model result](evidence/person2/desktop-official-domain.jpg)
- [Synthetic Unicode result](evidence/person2/desktop-unicode.jpg)
- [API stopped and error shown](evidence/person2/backend-offline.jpg)
- [Mobile model result](evidence/person2/mobile-result.jpg)
- [Mobile validation error](evidence/person2/mobile-error.jpg)

Some desktop captures were taken before the final button-height/error-copy
refinement; the mobile result/error and recovered desktop result show the final
behavior. The single-page-style demo guide and these captures make the app
reviewable. Person 3 can use them as reference while performing their own
independent pass; no Person 3 sign-off is claimed here.
