> Updated final review: [person3-review.md](person3-review.md). Person 2 run06 checks and Person 3 technical review materials are supplied; older pending statements below retain historical context. Human teammate sign-off is not claimed.

# Person 1 classical milestone evaluation — 7 October 2026

The revised classical-path implementation and research handoff are complete for
local prototype review. The model is experimental and its score is uncalibrated.
This report is not a production accuracy claim or full project completion.

## Frozen model and data

- Version: `rf-v6-d5923fe7d93e-20261007`.
- Local file: `artifacts/revised-run06/classical.joblib`.
- SHA256: `a5a68744712975f0f5809dd6f13825eeb47dc4251153f3f65eadc2120727d3ed`.
- Random forest: 150 trees, selected depth 8, minimum leaf 2, seed 42.
- Six candidates selected by development balanced accuracy. Training-only
  class balancing and weight 3 for official-navigation examples. Threshold 0.5.
- Versioned `extended-v1` profile: original 18 features plus host digit count,
  path digit fraction, path segment count, path entropy, government suffix and
  exact known-brand-domain indicators. No feature overrides the verdict.
- Shared parser, Unicode 16 skeleton mapping, 12 brands / 17 legitimate domains.
  Schema, extractor and resource hashes checked before inference.

Partitions: 16,554 training, 2,343 selection, 2,328 calibration fit,
2,499 calibration review, 1,698 final. Canonical URL, connected group, actual
domain and domain skeleton overlaps are zero. The final excludes all domains
and skeletons from previously observed UCI and revision sets. It was opened
only after saving and hashing the artifact. No generated families are used in
training or selection. Final outcomes did not select a new threshold.

The development data combines historical UCI train/validation records and
previous revision records with an official PhishTank snapshot and reviewed
organization/documentation navigation seeds. The final contains 1,370 source-
verified phishing strings and 328 benign navigation candidates from eight
benign and 978 phishing domains. PhishTank final additions were verified from
9 July through 7 August 2026 and reported online in the 7 October snapshot;
this is not a forward temporal evaluation. Phishing pages were never fetched.
Navigation labels follow owning-domain links, not individual page certification.

## Held-out measured results

| Metric | Revised v6 | Previous run03 on exactly the same final |
|---|---:|---:|
| Accuracy | 90.81% | 74.26% |
| Precision | 98.48% | 79.62% |
| Phishing recall | 90.00% | 91.53% |
| F1 | 94.05% | 85.16% |
| False-positive rate | 5.79% | 97.87% |

Confusion matrix (actual rows benign/phishing, predicted columns benign/phishing):
`[[309, 19], [137, 1233]]`. The previous model was already frozen; this comparison
is descriptive and does not establish an isolated feature ablation or statistical
significance. Dataset/class/source composition differs from the earlier UCI report.

## Calibration review and explanation contract

Calibrators fit on their own partition and are evaluated on a different one:

| Output | Review Brier | Review log loss | Review false positives | Review recall |
|---|---:|---:|---:|---:|
| raw | 0.08046 | 0.27068 | 7.99% | 88.93% |
| sigmoid | 0.07670 | 0.25021 | 14.12% | 91.80% |
| isotonic | 0.07583 | 0.29322 | 10.76% | 91.13% |

Sigmoid/isotonic improve Brier score on this review sample but increase false
alarms. The sample has convenience-source/class proportions and few benign
organization groups. Neither establishes population calibration. The frozen
artifact retains raw forest probabilities and `calibrated=false`; fitted
calibrators are research comparisons only. SHAP remains class 1, probability
scale, with checked base-plus-contribution additivity. Twenty final URLs passed
FastAPI prediction and explanation checks, plus Unicode and malformed inputs.
These checks verify integration, not an additional accuracy sample.
Twenty live localhost requests measured median request time 28.69 ms,
inference 13.69 ms and explanation 14.45 ms. These are development-machine
timings, include parser/features in inference, and do not estimate deployment
performance. The live HTTP parity check compares model and SHAP outputs with
standalone inference; see `evidence/person1/http-acceptance.json`.

## Offline manipulation tests

| Family | Pairs | Original phishing recall | Variant phishing recall | Lost detections |
|---|---:|---:|---:|---:|
| homoglyph | 200 | 89.0% | 100.0% | 0 |
| subdomain | 200 | 90.0% | 97.5% | 0 |
| percent_encoding | 200 | 77.5% | 90.0% | 0 |

Percent encoding preserves the decoded path and skips existing percent escapes.
Homoglyph substitution changes the host and represents synthetic attack intent;
deceptive subdomains retain the registrable tenant domain. Strings are not live
verified attack pages. Counts are capped at the first 200 eligible final phishing
records per family. No family was used for generated augmentation or tuning;
naturally occurring obfuscation may already exist in source records.

## Known controls and error review

These previously observed controls are development diagnostics, not fresh evidence:

| URL/control | Previous score | Revised score |
|---|---:|---:|
| `paypal.com/login` | 85 | 25 |
| `github.com/juri2406/PhishX` | 99 | 55 |
| `github.com/` | 16 | 28 |
| `www.w3.org/TR/2023/REC-WCAG22-20231005/` | 98 | 30 |
| `pаypal.com/login` | 96 | 91 |

The GitHub repository path is still a false positive at score 55. One of the
four previously observed legitimate control URLs is falsely flagged (25%);
this tiny development control group is not a fresh false-positive estimate. PayPal login
and W3C navigation are improved, but exact known domains are never whitelisted
into a benign verdict. Nineteen final benign examples are false positives and
137 phishing examples are missed. Raw URL error lists remain local in the
ignored artifact directory. Seventy brand checks cover legitimate domains,
lookalikes, brand text in paths and deceptive subdomains; none measures model
accuracy or universal brand coverage.

Earlier v4 and v5 experiments failed broader navigation evaluation: FPR 31.69%
and 46.20% respectively. They were not promoted; their aggregate measured results
are retained in `evidence/person1/failed-experiments.json`. Their now-observed
final partitions enter subsequent development and are excluded from v6 final.

## Evidence and limits

Aggregate outputs: `evidence/person1/revised-model-results.json`,
`api-verification.json`, `brand-review.json`, and `failed-experiments.json`.
Use [the workflow](person1-revised-workflow.md) for sources, labeling and exact-
snapshot reproduction; [the handoff](model-handoff.md) for the local archive.
Raw sources, detailed URL errors and model binaries are excluded from Git.

This meets the plan's classical-model deliverables: reproducible preparation,
parser/features/skeleton matching, frozen artifact, real evaluation, separate
calibration review, initial robustness and verified application contract. It
has no target accuracy requirement; these measured limitations remain visible.
Eight benign final domains give narrow coverage, and labels/source artifacts
can bias generalization. Further representative data, known path false alarms,
population calibration, Char-CNN/cascade, live signals and deployment belong to
continued research. Person 3's independent review remains outstanding; do not
claim the overall 60% acceptance yet.
