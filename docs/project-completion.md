# PhishX release v7: local academic demo

The frozen candidate `cascade-release-v7-a89fff3e7d31` passed every registered
model-quality gate and is selected for the local Docker demo. Docker and developer
launchers now select this provider. Runtime and human acceptance are tracked below;
passing sampled evaluation does not certify production or whole-web accuracy.

## Run and share

Run `bash scripts/demo.sh` from the repository root and open
http://127.0.0.1:8080. Manage it with `bash scripts/demo.sh status`, `logs`, or `stop`.
Docker Desktop or Docker/Colima with Compose is required. Only localhost port 8080
is published. The backend runs as nonroot with a read-only root filesystem.
Live checks run only after an explicit click and never change the model score.

Model binaries and raw data stay out of Git. Extract the trusted private v7
handoff at the repository root into `artifacts/release-v7/`, and verify its
checksums against `docs/evidence/completion/release-v7-artifacts.json`.
Earlier classical handoffs are insufficient for v7. The old run06 instructions
are historical and remain useful only for explicit classical-model comparisons.

## Fresh measured evaluation

The plan was frozen before fitting/evaluation. Candidate selection used 19,538
fit records and 4,716 domain-disjoint review records; review groups have zero
overlap with upstream RF/CNN training/selection groups. The frozen v4 RF and CNN
were retained. A learned context fusion model uses their outputs, 24 numeric URL
features and frozen Tranco popularity context. Seeded training-only masking of
rank information at rate 0.25 was selected on review data; final inference uses
actual frozen context, never a whitelist or forced benign verdict.

Threshold: 0.5. Labels: 0 benign, 1 phishing. All six quality checks passed.

| Fresh cohort | Model | Benign / phishing | False positives / false negatives | Recall | FPR |
| --- | --- | --- | --- | --- | --- |
| Historical UCI | Prior RF v6 | 1000 / 1000 | 128 / 68 | 93.2% | 12.8% |
| Historical UCI | v7 | 1000 / 1000 | 1 / 11 | 98.9% | 0.10% |
| External sources | Prior RF v6 | 364 / 200 | 13 / 30 | 85.0% | 3.57% |
| External sources | v7 | 364 / 200 | 2 / 4 | 98.0% | 0.55% |

Gates: UCI recall >=90%, external recall >=88%, each FPR <=5%, recall decrease
against the prior RF <=2 percentage points on each cohort, and no FPR worsening.
Promotion recomputes these gates from confusion counts and rejects inconsistent
summaries or relaxed thresholds. Artifacts and inference feature code are hashed.
The complete measured report and predeclared plan are in `docs/evidence/completion/`.

Fresh UCI groups exclude 44,433 previously observed domain skeletons. The external
cohort excludes all 46,433 previously observed groups including that UCI sample;
it contains 40 new official organization domain groups plus 200 new phishing groups.
The fixed 80-seed list covers international institutions, universities, museums,
libraries and public services; first 40 eligible unused groups, up to 10 paths
each, were selected before predictions. No outcome-based replacements were made.

## Limits and earlier failures

These are convenience samples. Benign labels derive from reviewed owning-domain
navigation and HTTP/title/hash provenance, not proof that every page is safe.
Phishing labels derive from the historical 7 October PhishTank snapshot; target
pages were not visited. UCI is historical and deliberately balanced. Scores are
uncalibrated, not live-web risk probabilities. The two external false positives
and four misses remain genuine errors and were not removed from the report.

Tranco list 262W9 was acquired on 21 October 2026, after historical URL labels;
this is not forward-temporal validation. Domain rank is learned context, not
ownership or a safety override. Ranking source: https://tranco-list.eu/.
Raw ranking data and model binaries are private handoff material outside Git.

Earlier inspected holdouts became development data for later candidates. Earlier
external FPRs were 8.78% (02), 16.29% (v3), 6.02% (v4), 47.77% (v5), and 5.23%
(v6); all failed promotion and their reports remain available. Repeated revisions
are disclosed; v7 is not an independent replication or a universal accuracy claim.
Holdout manifests retain the legacy phrase "Frozen before neural training": for
v7, the RF/CNN encoders were already frozen, and the holdouts were frozen before
fusion fitting and final prediction. Old source hashes require matching revisions;
never edit a recorded hash to load incompatible model code.

## Explanations and live checks

Every v7 explanation evaluates the full frozen pipeline on 16 URL combinations
and computes exact Shapley values for protocol, host, path and query. Fragment is
held constant. The placeholder reference `http://a.b` is not labeled benign.
Signed contributions explain model-output differences relative to that reference;
they do not establish causation, ownership or website safety. The API exposes the
method, reference, baseline, contributions and additivity residual. Classical
TreeSHAP is not substituted for a CNN/fusion prediction.

Optional DNS/TLS/redirect/RDAP checks are separately requested; only target headers
are fetched, without analyzing page content. Their statuses may be unavailable.
Private/internal targets and unsafe redirect destinations are rejected.

## Acceptance status

The earlier classical Docker/browser evidence is preserved as historical evidence.
The v7 Docker images built and reached healthy status. Real HTTP scans matched
native macOS predictions and all four Shapley contributions in the Linux backend;
additivity residuals were below 1e-5. Malformed URLs, private live targets,
security headers, model/dotfile protection and example.com live observations
passed. The measured report is `docker-v7-http.json`.

The tracked suite passed 86 tests plus 11 subtests on macOS and again inside the Linux backend image with networking disabled. The frontend production build passed. Browser verification
confirmed v7 connected, the real synthetic-lookalike result, signed four-component
explanations, result focus/next Tab, and no horizontal overflow at 390px. Actual
v7 screenshots and an agent review record are stored separately from old evidence. Human acceptance
is pending the user's actual H1-H8 checks in `docs/human-acceptance.md`. Remote CI
status must be confirmed against the actual GitHub run, separately from local tests.
No human signature or production readiness is claimed.
