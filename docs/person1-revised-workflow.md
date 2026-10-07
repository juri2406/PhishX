# Person 1 revised research workflow

The revised experiment broadens the historical UCI URL data with official
navigation candidates and a PhishTank feed snapshot retrieved on 7 October
2026. All target phishing URLs remain text and are never visited.

## Sources and labeling

- UCI PhiUSIIL: historical labels, CC BY 4.0; only original training and
  validation rows from run02 enter development. The old test and 4,000-row
  fresh diagnostic sample do not enter training.
- [PhishTank developer feed](https://www.phishtank.org/developer_info.php):
  `verified=yes` and `online=yes` as reported by the source, with explicit
  verification-date filters and a maximum of 20 URLs per domain skeleton.
  Source verification time is not the URL's creation date. Current page status
  is not independently fetched. Consult current source terms before reuse;
  no raw feed is redistributed in Git.
- Official documentation/organization navigation: fixed reviewed seed lists
  in `data/benign_navigation_sources*.json`. Only seed pages are fetched.
  Same-host, query-free links are retained as benign candidates, with page
  titles, status codes and HTML hashes. This is a source-based label basis,
  not an independent certification of every linked page or immunity from
  compromise. Blocked, empty, failed or off-domain-redirect sources are excluded.

## Reproduce the recorded snapshots

Use the exact ignored raw snapshots and their recorded checksums to reproduce
the metrics. Refetching a live feed or changed navigation page creates a new
dataset and requires a new run/version; it does not reproduce these numbers.
No raw source datasets, secrets, raw URL records or binary model weights are added to Git.

In a new environment, install the recorded ML and backend requirements as in
the existing setup guide. From the repository root on macOS/Linux:

```sh
export PYTHONPATH="$PWD/ml:$PWD"
```

On Windows set `$env:PYTHONPATH="$PWD\ml;$PWD"` and substitute
`.venv\Scripts\python.exe` for `.venv/bin/python`.

The official PhishTank download uses a descriptive user agent:

```sh
curl --fail --location --user-agent 'PhishX research dataset import (local student prototype)' \
  https://data.phishtank.com/data/online-valid.json.bz2 \
  --output data/raw/phishtank-20261007.json.bz2
.venv/bin/python scripts/collect_review_data.py data/benign_navigation_sources.json data/raw/official-navigation-20261007.csv
.venv/bin/python scripts/prepare_revised.py data/processed/revised-run04
.venv/bin/python scripts/train_revised.py data/processed/revised-run04 artifacts/revised-run04
```

Run04 exposed generalization failures and is preserved as a failed experiment.
Once observed, its final records may inform subsequent development but must
never again be described as untouched final evidence.

For the second experiment:

```sh
.venv/bin/python scripts/collect_review_data.py data/benign_navigation_sources_v5.json data/raw/official-navigation-v5-20261007.csv
.venv/bin/python scripts/prepare_revised.py data/processed/revised-run05 --round 5
.venv/bin/python scripts/train_revised.py data/processed/revised-run05 artifacts/revised-run05
.venv/bin/python scripts/report_revised.py data/processed/revised-run05 artifacts/revised-run05/classical.joblib docs/evidence/person1/revised-model-results.json
.venv/bin/python scripts/review_brands.py docs/evidence/person1/brand-review.json
.venv/bin/python scripts/verify_model.py artifacts/revised-run05/classical.joblib data/processed/revised-run05/final.csv artifacts/revised-run05/api-verification.json
```

Outputs must be new; scripts reject existing output directories/files. The
snapshot-specific preparation script also rejects stale intermediate files.
Use a clean checkout/work directory when reproducing, and keep recorded runs
for comparison.

## Freeze and calibration policy

Connected domain, origin and Unicode-skeleton groups define five partitions:
training, model selection, calibration fit, calibration review and final.
Previously observed UCI/run04 groups are excluded from run05's final. An
artifact is saved and hashed before final prediction. Hyperparameters use
selection data only. Threshold is fixed at 0.5; final outcomes never select it.

Run05 gives official-navigation training rows weight 3 and chooses among six
random forests by validation balanced accuracy. These changes were fixed
before opening the new final results. The comparison with the previous served
model uses exactly the same final records after both models are frozen.

Sigmoid and isotonic calibrators fit on a separate calibration partition and
are reviewed on another one. Their assessment does not establish deployment
calibration on this convenience-sample/class mix. The served candidate retains
raw forest probabilities, label 1, the frozen profile and the existing probability
SHAP contract. A future served calibrator requires new end-to-end explanation
checks; do not silently transform the probabilities.

The starter brand registry covers 12 brands and 17 domains. Seventy checks
cover exact legitimate domains, synthetic lookalikes, deceptive subdomains and
brand names only in paths. Exact-domain exclusion applies to the impersonation
signal, never to the model's verdict. Universal brand coverage, live domain
lookups, cascade and deployment remain outside this classical milestone.

## Third experiment: versioned feature extension

Run05 also failed. After inspecting that result, all its partitions became
development data; all run04/run05 groups and old UCI observed groups are
excluded from the new final. Run06 uses 24 features through `extended-v1`,
including separate host/path digits, path structure/entropy and two explicit
domain-category signals. No indicator forces a benign or phishing verdict.

```sh
.venv/bin/python scripts/collect_review_data.py data/benign_navigation_sources_v6.json data/raw/official-navigation-v6-20261007.csv
.venv/bin/python scripts/prepare_revised.py data/processed/revised-run06 --round 6
.venv/bin/python scripts/train_revised.py data/processed/revised-run06 artifacts/revised-run06
.venv/bin/python scripts/report_revised.py data/processed/revised-run06 artifacts/revised-run06/classical.joblib docs/evidence/person1/revised-model-results.json
.venv/bin/python scripts/verify_model.py artifacts/revised-run06/classical.joblib data/processed/revised-run06/final.csv artifacts/revised-run06/api-verification.json
```

Run06 adds PhishTank source verification dates from 9 July to 7 August 2026,
with `online=yes` reported in the October snapshot. It is a new-domain/source
evaluation, not a forward temporal test. A later snapshot cannot recreate it.
The run06 manifest stores accepted seed titles, collection checksums, input and
partition hashes. Local raw manifests retain full page hashes and link lists.
The run04 invocation originally used intermediate names without the `v4`
suffix; subsequent scripts use a round-specific name. Intermediate names do
not affect CSV content or split policy. Current checksum-protected inference
supports old 18-feature bundles and the new 24-feature bundle.

See [run06](evaluation-run06.md) for measured results, failed experiments,
calibration decision, known false positives and coverage limitations. No new
model tuning follows the run06 final.

## Private snapshot handoff

Run `python scripts/package_revised_handoff.py` with the same PYTHONPATH after
verification. It creates an ignored model ZIP and a separate ignored
`artifacts/handoff/PhishX_research_snapshots_v6.zip`. The latter supplies the
exact UCI development/sample CSVs, three navigation snapshots/manifests and
PhishTank feed needed for the recorded preparation, with SHA256 for every
file. It contains raw datasets and must never be committed to Git. Extract
into a fresh checkout, then reproduce run04, run05 and run06 in order. Follow
source attribution/terms; this local package is not a public dataset release.
The benign navigation alternative supplies paths missing from a top-domain
list; no Tranco snapshot is used or claimed in these runs.
