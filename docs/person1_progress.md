# Current Person 1 status — 7 October 2026

The **classical-path deliverables in the 60% plan are implemented and measured**.
This does not complete future Person 1 Char-CNN/cascade, live signals or final
deployment research, and does not claim the overall 60% acceptance. Person 3's
independent fixture/review is still outstanding.

| Plan deliverable | Evidence |
|---|---|
| Data/provenance/cleaning and reproducible groups | Revised workflow and frozen manifest in evidence/person1/revised-model-results.json |
| Shared parser and numeric feature schema | Base 18 plus versioned 24-feature extension; compatibility and parser tests |
| Unicode skeleton and starter brands | Unicode 16 map; 12 brands, 17 domains, 70 reviewed checks |
| Frozen classical model and inference wrapper | Run06 checksum and trusted local handoff; backend uses the same extractor |
| Validation selection and real held-out metrics | 1,698 untouched final records; full metrics and confusion matrix |
| Calibration review | Separate fitting/review partitions; raw, sigmoid, isotonic measured; output remains uncalibrated |
| Initial manipulation evaluation | 200 pairs each for three families, after artifact freeze; no generated augmentation |
| Integration support | 20 held-out API/SHAP checks; feature order, class 1, probability scale/additivity, malformed and Unicode checks |

Accuracy 90.81%, phishing recall 90%, precision 98.48%, F1 94.05%, FPR 5.79%.
The GitHub repository path still scores 55, a known false positive. Eight benign
final domains and source-based labels limit generalization. These are disclosed
limitations of an experimental baseline, not resolved detection guarantees.

Validation: 51 tests and 11 subtests pass, no skipped tests; frontend production
build passes. See [evaluation-run06.md](evaluation-run06.md),
[person1-revised-workflow.md](person1-revised-workflow.md) and
[model-handoff.md](model-handoff.md). The following sections retain earlier history.

# Person 1 progress

## Implemented

- Shared HTTP/HTTPS parser with Unicode and IDNA handling.
- Lexical, structural, encoding, skeleton, and brand-distance features.
- Offline Unicode mapping and a curated starter brand list.
- CSV provenance contract, duplicate/conflict filtering, and domain-group partitions.
- Classical baseline training, validation selection, held-out evaluation, and model export.
- Inference wrapper with feature/resource compatibility checks.
- Automated parser and synthetic pipeline checks.

## Previous research backlog (superseded by the 7 October evidence)

1. Add independently reviewed benign navigation URLs and an independent recent
   phishing source. Known PayPal/GitHub paths still produce false alarms.
2. Improve data coverage without tuning against the final fresh test set.
3. Review probability calibration using separate validation data and revisit the
   SHAP scale contract if the served probability is transformed.
4. Use another untouched evaluation set after any subsequent model change.
5. Complete brand-domain coverage and error-case review before finalizing the
   Person 1 handoff. Keep the current artifact explicitly experimental.

The classical implementation and initial research evidence are available. This
still does not establish full 60 percent project completion.

## Validation on 6 October 2026

Combined check: `.venv/bin/python -m pytest tests backend/tests -q` completed
with 36 passed and 1 skipped (optional SHAP dependency absent). The integration
check also passed after adding a real provider call through FastAPI /scan using
a synthetic artifact. This checks the contract only, not detection accuracy.
`pip check` reports no broken requirements. The tested Person 1 dependency
versions are recorded in `ml/requirements-verified.txt`.


## Real data work completed on 6 October 2026

- Opened the project and run guide in VS Code and added test/train/analysis tasks
  plus a model backend debug configuration. Direct native UI control was not
  available; the same workspace files were edited and executed through tools.
- Downloaded the official UCI PhiUSIIL archive and retained its checksum and
  CC BY 4.0 attribution. Imported a seeded 10,000-row URL-only sample.
- Corrected shared-host parsing, removed 3 duplicates, rejected 1 overlong URL,
  and split 9,996 records with no canonical/domain/group/skeleton overlap.
- Trained and froze the first baseline. Sanity checks exposed spurious formatting
  dependence. Retained its report as evaluation-run02.md.
- Corrected canonical feature formatting and added extractor compatibility hashes.
  Four equivalent PayPal root URL forms now produce the same features and score.
- Retrained into artifacts/uci-run03 and evaluated 4,000 fresh domain-disjoint
  records: accuracy 95.25%, phishing recall 92.55%, precision 97.83%, FPR 2.05%.
- Ran 200 offline synthetic variants per family on the fresh records. Observed
  recall: homoglyph 99%, subdomain 100%, percent encoding 100%. These generated
  tests do not establish verified live attacks or universal unseen robustness.
- Verified model-mode FastAPI/SHAP on 20 fresh URLs, plus Unicode and malformed
  input checks. Probability remains uncalibrated. Report: evaluation-run03.md.
- Validation: 46 tests passed, including SHAP checks. No skipped tests. pip check
  reports no broken requirements. Recorded versions include SHAP and dependencies.

The lower fresh result and remaining path false alarms are retained openly.
Do not use the higher original-source score as a deployment claim. Raw data,
model binaries and detailed evaluation outputs stay in ignored local directories.
