> Current review model: run06, 24-feature extended profile. Receive the trusted
> [revised handoff](model-handoff.md), use the default **PhishX model backend**
> VS Code task, and follow [the revised workflow](person1-revised-workflow.md)
> for new-source training. The older UCI training commands below retain the
> 18-feature baseline for historical reproduction.

# PhishX

Person 1's initial implementation: offline URL normalization, lexical and structural features, Unicode skeleton brand matching, dataset cleaning, domain-separated splits, classical model training, evaluation, and an inference wrapper.

## Setup

Requires Python 3.10 or newer. From the project directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
phishx analyze 'https://pаypal-secure-login.com'
```

`analyze` returns features and brand evidence. It does not return a phishing verdict before a model has been trained. Input URLs are never fetched or resolved. An omitted scheme is treated as HTTPS for parsing, but does not count as observed HTTPS evidence.

## Prepare real data

Create a CSV following `data/input_template.csv`. Required columns:

- `url`: full URL or hostname.
- `label`: 0 for benign, 1 for phishing, supported by source evidence.
- `source`: provenance, including snapshot/version or source record ID where possible.
- `collected_at`: collection date or timestamp.
- `group_domain`: optional original base domain for synthetic variants. All variants must share the base domain's group.
- `family`: optional manipulation family, otherwise `original`.

Do not populate the training set from test fixtures. PhishTank/OpenPhish phishing records and vetted Tranco benign candidates are the planned sources. Top-site membership alone does not guarantee a benign label. Preserve dataset license/usage terms and source dates alongside the raw snapshot. Raw data and model outputs are ignored by Git.

```sh
phishx prepare data/raw/labeled_urls.csv data/processed/run01
phishx train data/processed/run01 artifacts/run01
phishx predict 'https://pаypal.com' --model artifacts/run01/classical.joblib
```

Preparation rejects invalid rows, removes duplicate URLs, excludes conflicting labels, and groups by registrable domain including private PSL suffixes. Splits target approximately 70/15/15 percent of domain groups. They are not guaranteed to have that exact fraction of rows. Every split must contain both labels. The manifest records exclusions, class counts, seed, and input checksum. Use a new output directory for each run.

Training selects random-forest depth on validation F1 and evaluates the frozen selection against a dummy baseline on the test partition. It exports the model, ordered feature schema, resource checksums, and actual metrics. Probabilities are uncalibrated; risk score is rounded probability × 100, not proof that a URL is safe or malicious. Load only trusted joblib files.

## Person 2 integration

```python
from phishx import analyze_url
from phishx.model import predict
analysis = analyze_url(url)
result = predict(url, 'artifacts/run01/classical.joblib')
```

FastAPI should validate errors from `InvalidURL`. Reuse this extractor rather than implementing another parser. The current prediction helper loads an artifact per call; Person 2 should cache the verified bundle at application startup for serving. SHAP, FastAPI, frontend, domain lookups, and the Char-CNN cascade are not implemented here.

## Scope and evidence

The starter brand list covers 12 brands and selected domains, not every legitimate regional domain. Skeleton similarity is a feature, not a standalone phishing decision. The NFD/map/NFD comparison uses Unicode 16.0.0 data; it does not implement full bidi skeleton processing. tldextract uses its packaged offline PSL snapshot. Unknown suffixes fall back to the last two labels and need review during data cleaning.

Tests use synthetic records solely to verify parsing, leakage prevention, training, and inference. There are no real-data performance claims yet. Remaining Person 1 work is tracked in `docs/person1_progress.md`.

## Primary references

- Unicode security mechanism: https://www.unicode.org/reports/tr39/
- Versioned mapping data: https://www.unicode.org/Public/security/16.0.0/confusables.txt
- Public Suffix List: https://publicsuffix.org/list/
- GroupShuffleSplit: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html

Unicode mapping data retains its upstream copyright/license header. See its linked Unicode terms before redistribution. No project license has been selected yet.

## Import source exports

Download source exports from their official services, record the source date and access/license terms, and review benign candidates before importing. This helper handles a verified/online PhishTank JSON export or an OpenPhish text export and a reviewed Tranco rank/domain CSV:

```sh
python scripts/import_sources.py --phishing data/raw/phishtank.json --format phishtank --benign data/raw/reviewed_tranco.csv --benign-reviewed --output data/raw/labeled_urls.csv
```

For OpenPhish, change the format to `openphish` and supply its text export. Import timestamps and input hashes appear in the adjacent `.sources.json` file; keep original source collection dates in your dataset records if different from the import date. The importer does not validate source licenses or independently verify URL labels.

## Import local source exports

After reviewing the benign labels, convert an official PhishTank JSON export or
OpenPhish text export with a reviewed Tranco rank/domain CSV:

```sh
python scripts/import_sources.py --phishing data/raw/phishtank.json --format phishtank --benign data/raw/reviewed_tranco.csv --benign-reviewed --output data/raw/labeled_urls.csv
```

The importer saves input checksums and the import timestamp in a companion
sources JSON file. Preserve source snapshot dates and usage terms separately.
Change `--format` to `openphish` for a plain URL-per-line feed. It does not
independently verify labels or source licenses. Training and API parsing share
a 2048-character limit. For the existing backend, configure
`PHISHX_PROVIDER=ml.integration:create_provider` and `PHISHX_MODEL_PATH`.
