# Person 3 final-stage technical review

**Branch:** `aniruth`. **Date:** 21 October 2026.
**Reviewer:** Codex assistant, at the user's request. No human Aniruth/teammate
attendance, signature, approval or independent human audit is asserted.

The requested independent fixture, real browser/API review, defect report,
six new screenshots and one-page guide are supplied. Person 3 did not change
training data, detector code, model weights, thresholds, predictions or SHAP
reasons. A review deliverable can be complete while model-quality and deployment
issues remain open. This does not certify a production-ready project.

## Independent fixture and provenance

The fixture was fixed before either model's predictions. It has six benign
publisher candidates, six source-labelled phishing examples, four synthetic
Unicode lookalikes and four malformed inputs. The 12 real URL domain-skeleton
groups have **zero overlap** with all processed datasets (including the new
neural holdout), both previously observed UCI samples and the earlier Person 3
fixture. No case was removed or replaced because of its outcome.

The benign sources were checked through their actual HTTP status, page title
and HTML hash, and reviewed on their publisher pages:
[Haxe](https://haxe.org/manual/),
[MariaDB](https://mariadb.org/documentation/),
[fish](https://fishshell.com/docs/current/),
[Alpine Linux](https://alpinelinux.org/about/),
[Crystal](https://crystal-lang.org/) and
[Gleam](https://gleam.run/documentation/).
All six returned HTTP 200 with inspectable titles. Official ownership is a
candidate label basis, not proof that a site can never be compromised.

The phishing cases are selected by a fixed SHA256 order from unused domain
skeletons in the PhishTank snapshot collected 7 October. The source reports
`verified=yes` and `online=yes`; verification dates range from August 2024 to
June 2026. Their target pages were never visited, including during live checks.
These are historical source labels, not current independent live-page judgments.
Synthetic `.example` strings are explicitly not verified real attacks.

Raw fixture URLs and complete browser/API responses stay in the ignored
`artifacts/handoff/PhishX_person3_final_review.zip`. Committed cases use IDs,
URL hashes, label provenance and actual results, never raw phishing URLs.
The private ZIP is not a public dataset release.

## Actual results

| Check | Classical v6 | Research cascade |
|---|---:|---:|
| Browser / HTTP / standalone application parity | 20/20 | 20/20 |
| Source-labelled benign false positives | 1/6 | 0/6 |
| Source-labelled phishing misses | 2/6 | 0/6 |
| Malformed inputs rejected with visible error / HTTP 422 | 4/4 | 4/4 |

**Application parity is not detection accuracy.** Six benign and six phishing
examples form a small convenience regression fixture, not a representative
benchmark. The cascade's stronger showing here does not overturn the much
larger broader-source false-positive regression recorded by Person 1.

Classical benign case 5 (Crystal) has probability 0.5013106552878407 and rounded
score 50, just above the fixed 0.5 classification threshold. Phishing cases 2
and 6 score 47 and 32. These outcomes are retained. No benign whitelist or
score adjustment was added. Synthetic string scores are not counted as real
attack accuracy.

All 16 valid results per model matched standalone probability, normalized host,
model route and explanation contract. In the cascade, 11 of those 16 used the
CNN and correctly showed no substituted SHAP reasons; five stayed classical
and retained RF explanations. Browser observations match the real HTTP outputs.

Evidence:

- [Redacted results and per-case checks](evidence/person3-final/fixture-results.json)
- [40-row comparison CSV](person3-final-fixture-results.csv)
- [Frozen fixture manifest](evidence/person3-final/manifest.json)
- [Source checks](evidence/person3-final/source-review.json)
- [Actual UI observations](evidence/person3-final/ui-observations.json)

## Browser and live-check pass

The default interface used classical v6 on port 5173/API 8000. A separate
interface on 5174/API 8001 connected the explicit research provider; the default
model was not changed. The browser showed the research warning, correct route,
unavailable neural explanations and disabled live checks for that server.

Observed live-check behavior on the default server:

- `https://example.com/`: actual DNS answers, TLS validation, zero HEAD redirects
  and RDAP age returned available. These observations remain separate from the
  model score and are point-in-time, not a safety claim.
- `http://127.0.0.1/`: the text scan was allowed, but live access was blocked
  with a useful public-target validation error. No private page was fetched.
- `http://example.com/`: TLS was `not_applicable`, not falsely described as valid.
- A reserved `.invalid` hostname: unavailable DNS/TLS/redirect/registration states.
- During a deliberately paused review API, the live button was disabled with a
  loading message. The client subsequently reported its timeout. The process
  was resumed and retry succeeded. This forced failure is not a latency sample.
- Stopping only the actual default API left the frontend available. Reload
  displayed backend-unreachable guidance, a scan displayed a useful response
  error, and restoring the API plus Retry connection recovered successfully.

Keyboard Enter submitted successfully. A background automated focus read did
not establish retained focus on the result region; no focus-pass claim is made.
Mobile validation and research-result pages were measured at width 390 px with
scroll width 390 px, with no horizontal overflow. This is a focused desktop and
mobile review, not comprehensive browser/accessibility certification.

## Defects and disposition

| ID | Finding | Owner / disposition |
|---|---|---|
| MODEL-FINAL-01 | Crystal false positive, probability just above 0.5 | Person 1; retained open research finding |
| MODEL-FINAL-02 | Two historical source-labelled phishing misses | Person 1; retained open research finding |
| MODEL-FINAL-03 | Cascade broader-source FPR 20.73% versus classical 5.79% | Person 1; blocks promotion despite this small fixture |
| UX-FINAL-01 | Text-model section still says "Unavailable signals" when separately requested live observations become available below | Person 2; clarify scope in a future UI refinement |
| A11Y-FINAL-01 | Retained result focus not established by automated observation | Person 2/manual follow-up; Enter submission itself verified |
| DEPLOY-FINAL-01 | Docker build/hosting not verified on this Mac | Person 2; not closed by these local tests |

No new application prediction/SHAP parity defect was observed in the 40-case
pass. Open model and UX findings are not concealed by application pass counts.
No model was retrained or test fixture relabelled after this review.

## Six original screenshots

- [Desktop empty state](evidence/person3-final/desktop-empty.jpg)
- [Real benign classical result](evidence/person3-final/desktop-benign.jpg)
- [Real live checks](evidence/person3-final/desktop-live-checks.jpg)
- [Mobile malformed-input error](evidence/person3-final/mobile-validation.jpg)
- [Mobile research warning / unavailable neural explanation](evidence/person3-final/mobile-cascade.jpg)
- [Actual backend offline](evidence/person3-final/backend-offline.jpg)

These are new native browser captures, visually inspected. No phishing target
URL is exposed in them. The older classical milestone images were not reused
as evidence of this new work.

## Guide, reproduction and boundaries

[Updated one-page guide](person3-final-user-guide.pdf) covers startup, score
bands, optional live checks, research limitations and recovery. It was rendered
and visually checked as one page.

Use `scripts/prepare_person3_final_fixture.py` on the matching private source
snapshots before predictions. Existing outputs are rejected. With the two model
APIs running, execute `scripts/review_person3_final.py` against the frozen CSV.
Browser interactions were performed through the actual browser controls; they
are not replaced by test-client or synthetic screenshots. Their private JSON
observations are included in the handoff for audit.

The guide and this report are review material. A human teammate can assess the
findings, but no human sign-off is invented. Final hosting, comprehensive
accessibility validation and neural promotion remain project completion gates.

Verification on this branch: 77 Python tests and 11 subtests passed; frontend
production build passed; git diff --check passed. The private review ZIP
contains 22 files verified against its SHA256 manifest.
