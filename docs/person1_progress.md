# Person 1 progress

## Implemented

- Shared HTTP/HTTPS parser with Unicode and IDNA handling.
- Lexical, structural, encoding, skeleton, and brand-distance features.
- Offline Unicode mapping and a curated starter brand list.
- CSV provenance contract, duplicate/conflict filtering, and domain-group partitions.
- Classical baseline training, validation selection, held-out evaluation, and model export.
- Inference wrapper with feature/resource compatibility checks.
- Automated parser and synthetic pipeline checks.

## Remaining before milestone completion

1. Obtain dated, licensed phishing and benign source snapshots and populate the input CSV.
2. Review labels and source balance. Keep source identity out of model features.
3. Audit known-suffix coverage, legitimate brand-domain coverage, and domain/skeleton relatedness across partitions.
4. Run preparation and train on real data, inspect rejection manifest and per-class metrics.
5. Reserve an unseen manipulation family before augmentation or threshold selection.
6. Add measured per-family robustness evaluation and inspect false positives.
7. Check probability calibration on validation data and freeze the final artifact.
8. Hand the artifact, feature schema, resource versions, and evaluation report to Person 2.

The local code is a first implementation, not completion of all Person 1 work or a claim of 60 percent project completion.

## Validation on 6 October 2026

Combined check: `.venv/bin/python -m pytest tests backend/tests -q` completed
with 36 passed and 1 skipped (optional SHAP dependency absent). The integration
check also passed after adding a real provider call through FastAPI /scan using
a synthetic artifact. This checks the contract only, not detection accuracy.
`pip check` reports no broken requirements. The tested Person 1 dependency
versions are recorded in `ml/requirements-verified.txt`.
