"""Publish aggregate evidence for the corrected model and fresh holdout."""
import argparse
import json
from pathlib import Path


def write_report(model_dir, output):
    root=Path(model_dir)
    e=json.loads((root/'evaluation.json').read_text())
    fresh=json.loads((root/'fresh-evaluation.json').read_text())
    verification_path=root/'api-verification-fresh.json'
    verification=json.loads(verification_path.read_text()) if verification_path.exists() else None
    if fresh['artifact_sha256']!=e['artifact_sha256']:
        raise ValueError('Artifact checksums differ')
    metric=fresh['test']; manifest=e['dataset_manifest']
    lines=['# PhishX corrected baseline and fresh evaluation','',
           '## Outcome','',
           'A trained classical model, frozen artifact, shared extractor and functioning SHAP/API integration are available locally. This is an experimental baseline. Known official-domain paths still produce false alarms, so it is not ready to claim general-purpose detection quality.',
           '', '## Source and partitions','',
           '[UCI PhiUSIIL](https://archive.ics.uci.edu/dataset/967/phiusil-phishing-url-dataset), Prasad and Chandra (2024), CC BY 4.0. DOI: https://doi.org/10.1016/j.cose.2023.103545. Only URL and label columns are imported; the source labels are inverted to 0 benign and 1 phishing. Individual collection dates are unknown.',
           '',f"Initial sample: 10,000 rows, {manifest['accepted_rows']:,} after cleaning. Training uses {e['rows']['train']:,} rows and validation {e['rows']['validation']:,}. Domains, origin groups, canonical URLs and exact skeleton matches do not overlap across initial partitions.",
           '',f"Fresh evaluation imports {fresh['input_rows']:,} records after excluding all initial-run domain/skeleton groups, including the initial validation and test groups. After canonical duplicate/conflict removal, {metric['rows']:,} remain, with {metric['benign_rows']:,} benign and {metric['phishing_rows']:,} phishing labels. Prior-domain/skeleton overlap is {fresh['prior_domain_skeleton_overlap']}.",
           '',fresh['caveat'], '', '## Formatting correction','',
           'The first model gave www.paypal.com a score of 13 without a slash and 90 with a slash. Features now use a canonical URL, a consistent root slash, and exclude one leading www presentation prefix from lexical ML measurements. Reports retain the actual host. Four equivalent PayPal root forms now share an identical feature vector. Artifact loading checks extractor hashes, so the old baseline cannot silently run with the new extractor.',
           '', 'The original report is retained in evaluation-run02.md for comparison. Original-partition results for the corrected model are exploratory because the initial experiment informed the formatting correction. The fresh partition below is the primary new evaluation. No model changes or threshold tuning follow its results.',
           '', '## Fresh held out metrics','', '| Measure | Value |','|---|---:|']
    for name in ('accuracy','precision','recall','f1','false_positive_rate','roc_auc','brier_score','log_loss'):
        lines.append(f"| {name.replace('_',' ')} | {metric[name]:.4f} |")
    lines += ['',f"Confusion matrix, rows actual benign/phishing and columns predicted benign/phishing: `{metric['confusion_matrix']}`.",
              '', 'The random forest has 150 trees, minimum leaf size 2 and balanced class weights. Depth selection uses initial validation F1 only. Decision threshold remains 0.5. Scores remain uncalibrated. Brier score, log loss and probability bins are diagnostics, not proof of real-world calibration.',
              '', '## Frozen model stress tests on fresh records','', '| Generated family | Cases | Original recall on same cases | Variant recall | Lost detections |','|---|---:|---:|---:|---:|']
    for name,r in fresh['families'].items():
        if r['rows']:
            lines.append(f"| {name} | {r['rows']} | {r['paired_original_recall']:.4f} | {r['recall']:.4f} | {r['lost_detections']} |")
    lines += ['', 'These are synthetic offline URL-string perturbations, not verified live phishing pages. Homoglyph variants change the host. No generated family is used in training or validation, but naturally occurring attack examples may exist in the source. Results do not establish universal unseen-attack robustness.',
              '', '## Official domain formatting diagnostics','', '| URL string | Risk score | Predicted phishing |','|---|---:|---|']
    for control in fresh['known_domain_formatting_controls']:
        lines.append(f"| {control['url']} | {control['risk_score']} | {'Yes' if control['predicted_phishing'] else 'No'} |")
    lines += ['',fresh['control_caveat'], '',
              'The remaining errors on legitimate-looking paths expose source bias: the training source lacks representative benign navigation URLs. Add independently reviewed benign pages and fresh phishing sources, then use a new final evaluation set. Do not keep tuning against this fresh set.',
              '', '## API and explanation checks','']
    if verification:
        lines += [f"FastAPI model mode and SHAP explanations passed checks on {verification['real_heldout_urls_checked']} fresh held-out URLs. The class is explicitly phishing label 1; contributions explain probability output. SHAP additivity is checked for every explained row. Synthetic Unicode matching and malformed URL error mapping also passed.",
                  '', 'Any recorded request timings use in-process TestClient and do not represent network or deployed latency.']
    else:
        lines += ['API verification output is not present in this report.']
    lines += ['', '## Artifact and reproduction','',f"Model version: `{e['model_version']}`.",
              '',f"Artifact SHA256: `{e['artifact_sha256']}`.",
              '',f"Fresh input SHA256: `{fresh['external_input_sha256']}`.",
              '',f"Source ZIP SHA256: `{fresh['source']['downloaded_archive_sha256']}`.",
              '',f"Trusted local artifact: `{root}/classical.joblib`. Full evaluation, errors, calibration bins and verification records remain under ignored artifact directories. Reproduce using person1-vscode.md. Data and model binaries are not pushed to GitHub.",
              '', 'Remaining before the Person 1 handoff is final: representative benign-page data, an independent recent source, probability calibration review, and a new untouched final evaluation. The deep cascade, live domain signals and deployment remain later project work.', '']
    Path(output).write_text('\n'.join(lines))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('model_dir');p.add_argument('output')
    a=p.parse_args();write_report(a.model_dir,a.output)
