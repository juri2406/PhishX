# PhishX corrected baseline and fresh evaluation

## Outcome

A trained classical model, frozen artifact, shared extractor and functioning SHAP/API integration are available locally. This is an experimental baseline. Known official-domain paths still produce false alarms, so it is not ready to claim general-purpose detection quality.

## Source and partitions

[UCI PhiUSIIL](https://archive.ics.uci.edu/dataset/967/phiusil-phishing-url-dataset), Prasad and Chandra (2024), CC BY 4.0. DOI: https://doi.org/10.1016/j.cose.2023.103545. Only URL and label columns are imported; the source labels are inverted to 0 benign and 1 phishing. Individual collection dates are unknown.

Initial sample: 10,000 rows, 9,996 after cleaning. Training uses 6,957 rows and validation 1,509. Domains, origin groups, canonical URLs and exact skeleton matches do not overlap across initial partitions.

Fresh evaluation imports 4,000 records after excluding all initial-run domain/skeleton groups, including the initial validation and test groups. After canonical duplicate/conflict removal, 4,000 remain, with 2,000 benign and 2,000 phishing labels. Prior-domain/skeleton overlap is 0.

Fresh held-out records and domain groups, but the same historical UCI source. No external-source or temporal generalization claim.

## Formatting correction

The first model gave www.paypal.com a score of 13 without a slash and 90 with a slash. Features now use a canonical URL, a consistent root slash, and exclude one leading www presentation prefix from lexical ML measurements. Reports retain the actual host. Four equivalent PayPal root forms now share an identical feature vector. Artifact loading checks extractor hashes, so the old baseline cannot silently run with the new extractor.

The original report is retained in evaluation-run02.md for comparison. Original-partition results for the corrected model are exploratory because the initial experiment informed the formatting correction. The fresh partition below is the primary new evaluation. No model changes or threshold tuning follow its results.

## Fresh held out metrics

| Measure | Value |
|---|---:|
| accuracy | 0.9525 |
| precision | 0.9783 |
| recall | 0.9255 |
| f1 | 0.9512 |
| false positive rate | 0.0205 |
| roc auc | 0.9776 |
| brier score | 0.0394 |
| log loss | 0.1564 |

Confusion matrix, rows actual benign/phishing and columns predicted benign/phishing: `[[1959, 41], [149, 1851]]`.

The random forest has 150 trees, minimum leaf size 2 and balanced class weights. Depth selection uses initial validation F1 only. Decision threshold remains 0.5. Scores remain uncalibrated. Brier score, log loss and probability bins are diagnostics, not proof of real-world calibration.

## Frozen model stress tests on fresh records

| Generated family | Cases | Original recall on same cases | Variant recall | Lost detections |
|---|---:|---:|---:|---:|
| homoglyph | 200 | 0.9250 | 0.9900 | 0 |
| subdomain | 200 | 0.9200 | 1.0000 | 0 |
| percent_encoding | 200 | 1.0000 | 1.0000 | 0 |

These are synthetic offline URL-string perturbations, not verified live phishing pages. Homoglyph variants change the host. No generated family is used in training or validation, but naturally occurring attack examples may exist in the source. Results do not establish universal unseen-attack robustness.

## Official domain formatting diagnostics

| URL string | Risk score | Predicted phishing |
|---|---:|---|
| https://paypal.com | 13 | No |
| https://paypal.com/ | 13 | No |
| https://www.paypal.com | 13 | No |
| https://www.paypal.com/ | 13 | No |
| https://paypal.com/login | 85 | Yes |
| https://github.com/ | 16 | No |
| https://github.com/juri2406/PhishX | 99 | Yes |

Known official-domain URL-string controls. Content/current compromise status is not fetched or independently verified. These controls are diagnostic, not a new real-data accuracy benchmark.

The remaining errors on legitimate-looking paths expose source bias: the training source lacks representative benign navigation URLs. Add independently reviewed benign pages and fresh phishing sources, then use a new final evaluation set. Do not keep tuning against this fresh set.

## API and explanation checks

FastAPI model mode and SHAP explanations passed checks on 20 fresh held-out URLs. The class is explicitly phishing label 1; contributions explain probability output. SHAP additivity is checked for every explained row. Synthetic Unicode matching and malformed URL error mapping also passed.

Any recorded request timings use in-process TestClient and do not represent network or deployed latency.

## Artifact and reproduction

Model version: `rf-v2-1774537c789e-seed42`.

Artifact SHA256: `2b59557ed0a23220bd69e0f2775ad934d20fa1587ff71fe2decb750fb2ff8ac7`.

Fresh input SHA256: `19707e288a6e8dddb51c4d68cd0f08a10c681859211ce2ff396b62278491338f`.

Source ZIP SHA256: `0a639fd03aea6308c5b1c10c92aa23c2ce1505447a9137271865cd0badc9a59a`.

Trusted local artifact: `artifacts/uci-run03/classical.joblib`. Full evaluation, errors, calibration bins and verification records remain under ignored artifact directories. Reproduce using person1-vscode.md. Data and model binaries are not pushed to GitHub.

Remaining before the Person 1 handoff is final: representative benign-page data, an independent recent source, probability calibration review, and a new untouched final evaluation. The deep cascade, live domain signals and deployment remain later project work.
