# Local classical milestone evidence - 7 October 2026

The implementation and measured evidence for the six classical-path modules
in the plan are supplied. Person 2's run06 acceptance and Person 3's separate
fixture/review materials are complete as assistant-performed technical work.
No human teammate signature, attendance or formal assessment is manufactured.

| Module / plan weight | Acceptance evidence |
|---|---|
| Dataset preparation and leakage controls / 10% | person1-revised-workflow.md and evidence/person1/revised-model-results.json: manifests, provenance, hashes and zero group overlaps |
| Shared URL parser and features / 10% | tests, ordered 18/24 feature schema and artifact compatibility checks in person1-handoff.md |
| Skeleton / brand matching / 10% | Unicode 16 mapping; 12 brands / 17 domains and 70 checks in evidence/person1/brand-review.json |
| Classical model and evaluation / 10% | Frozen checksum, full held-out confusion matrix, precision/recall/F1/FPR in evaluation-run06.md |
| FastAPI / React application / 10% | person23-acceptance.md: fresh setup, real browser scans, errors, mobile and recovery |
| SHAP and initial robustness / 10% | Actual class-1 probability/additivity checks, 200 pairs per family and local measured timings |

These planning weights total the proposed 60% classical scope; they are not a
production-readiness score or a claim that later work exists. The remaining
40% is Char-CNN/cascade (20%), live domain signals/expanded robustness (10%)
and deployment/final validation (10%). No fixture-only output or invented
latency, screenshot, prediction or explanation is counted.

## Review package

Person 3's 20-case fixture has domain groups separate from recorded model
training and evaluation. See [the review](person3-review.md), its recorded
20 browser/HTTP observations, six actual screenshots, [one-page guide](person3-user-guide.pdf)
and [bug list](person3-review.md#bug-list-and-disposition). Full URL strings and
private responses are shared separately in the ignored review ZIP. The model
and exact research snapshots also stay outside Git.

Application parity passed 20/20; this is not 100% detection accuracy. The
separate source-labeled fixture exposed two false positives and one missed
phishing label. Run06's larger external-source final measured 90.81% accuracy,
90% recall and 5.79% FPR, with only eight benign domains. Source-label age,
convenience sampling, known false alarms and uncalibrated output remain
limitations. No blocking application defect was observed in the focused review.

All technical review materials are ready for the team's short review. If an
assessment requires an independent human reviewer or meeting attendance,
that human confirmation remains to be supplied by the team; this report does
not substitute an invented signature for it. Research limitations are retained
rather than silently changing the frozen model after fixture outcomes.


## Later-stage review, 21 October 2026

The 60% classical milestone remains a historical acceptance record. New live
checks and the opt-in neural research provider are reviewed separately in
[Person 3 final-stage report](person3-final-review.md). That report retains open
model, UX and deployment issues; it is not a claim that the full project is
production-ready.
