# PhishX first real data evaluation

This first model exposed severe false alarms on ordinary PayPal and GitHub URLs. It is retained as a baseline comparison, not a usable detector. The current extractor rejects this older artifact. See evaluation-run03.md for the correction and fresh evaluation.

## Dataset and method

Source: [UCI PhiUSIIL](https://archive.ics.uci.edu/dataset/967/phiusil-phishing-url-dataset). Prasad, A. and Chandra, S. (2024). PhiUSIIL Phishing URL (Website). UCI Machine Learning Repository. https://doi.org/10.1016/j.cose.2023.103545

License: CC BY 4.0. UCI labels are inverted to PhishX convention: 0 benign, 1 phishing. Only URLs and labels are imported. All 18 features are recomputed by PhishX.

The seeded sample contains 10,000 input rows. Cleaning retains 9,996, removes 3 duplicates and 0 conflicting URLs, and rejects 1 invalid record.

The splitter joins registrable domains, supplied origin groups, and exact Unicode skeleton matches. Cross-partition canonical URL, actual domain, group and skeleton overlap counts: {'group_domain': 0, 'actual_domain': 0, 'domain_skeleton': 0, 'canonical': 0}.

| Split | Rows | Benign | Phishing | Groups |
|---|---:|---:|---:|---:|
| train | 6957 | 3478 | 3479 | 6277 |
| validation | 1509 | 755 | 754 | 1345 |
| test | 1530 | 767 | 763 | 1346 |

Random forest: 150 trees, selected max depth 16, leaf minimum 2, balanced class weights, seed 42. Selection uses validation F1 only. Decision threshold is fixed at 0.5. Test rows do not select hyperparameters.

## Held out results

| Measure | Random forest | Dummy baseline | HTTPS only diagnostic |
|---|---:|---:|---:|
| accuracy | 0.9941 | 0.4987 | 0.7425 |
| precision | 0.9987 | 0.4987 | 1.0000 |
| recall | 0.9895 | 1.0000 | 0.4836 |
| f1 | 0.9941 | 0.6655 | 0.6519 |
| false positive rate | 0.0013 | 1.0000 | 0.0000 |
| roc auc | 0.9987 | 0.5000 | 0.7418 |
| brier score | 0.0051 | 0.2500 | 0.1702 |
| log loss | 0.0337 | 0.6931 | 0.4862 |

Confusion matrix, rows actual benign/phishing and columns predicted benign/phishing: `[[766, 1], [8, 755]]`.

The HTTPS-only classifier is a source-bias diagnostic. If it performs well, those results do not establish robustness against phishing sites that use HTTPS.

## Synthetic stress tests

| Family | Cases | Original recall on same cases | Variant recall | Lost detections |
|---|---:|---:|---:|---:|
| homoglyph | 200 | 0.9900 | 1.0000 | 0 |
| subdomain | 200 | 0.9900 | 1.0000 | 0 |
| percent_encoding | 200 | 1.0000 | 1.0000 | 0 |

Synthetic offline URL-string perturbations, not verified live phishing pages. Homoglyph domains change the host; labels reflect attack intent only. No claim that a family is absent naturally from source data.

No generated family enters training or validation. Homoglyph is reserved from generation until frozen-model evaluation. This is an unseen generated-family check, not evidence that naturally occurring examples of the family were absent from the original dataset.

## Probability and deployment limits

The artifact remains uncalibrated. Brier score, log loss, and reliability bins are diagnostic checks, not proof of calibration. The class-balanced historical sample does not reproduce real-world phishing prevalence. No probability-calibration mapping has been fitted.

The source was donated in 2024 and does not provide collection dates for individual rows. These results do not demonstrate present-day or temporal generalization. Subdomain changes and encoded paths are offline perturbations; altered homoglyph domains are hypothetical attack strings rather than verified live phishing URLs.

Unknown suffix rows: 0. A zero count checks suffix coverage only; it does not validate labels or the full brand list.

## Reproduction and handoff

Model version: `rf-1774537c789e-seed42`.

Artifact SHA256: `0fa671330cc8fc1712ec8d14f0f31bb1218350b31a206485a4bfc68c93c4978f`.

Input CSV SHA256: `1774537c789e58c95ee5d52a76c61a7c18c4b23ba2d40866a62117e9583393aa`.

UCI ZIP SHA256: `0a639fd03aea6308c5b1c10c92aa23c2ce1505447a9137271865cd0badc9a59a`.

Local artifact: `artifacts/uci-run02/classical.joblib`. Full evaluation, probability bins, error cases and generated variants remain under ignored artifact directories. Reproduce them using `docs/person1-vscode.md`. Raw records and model binaries are not committed.

The classical detector does not implement the deep-model cascade, live domain signals, or deployment. This report alone does not establish the full 60 percent milestone.
