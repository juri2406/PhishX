"""Write an aggregate Markdown report without publishing dataset URLs."""
import argparse
import json
from pathlib import Path


def write_report(model_dir, robustness_dir, output):
    model_dir=Path(model_dir); robustness_dir=Path(robustness_dir)
    evaluation=json.loads((model_dir/'evaluation.json').read_text())
    robustness=json.loads((robustness_dir/'robustness.json').read_text())
    manifest=evaluation['dataset_manifest']
    if evaluation['model_version'] != robustness['model_version']:
        raise ValueError('Evaluation and robustness model versions must match')
    metrics=evaluation['test']; source=manifest.get('source_provenance') or {}
    lines=['# PhishX first real data evaluation','',
           '## Dataset and method','',
           f"Source: [UCI PhiUSIIL]({source.get('dataset_url','https://archive.ics.uci.edu/dataset/967/phiusil-phishing-url-dataset')}). {source.get('citation','')}",
           '',f"License: {source.get('license','not recorded')}. UCI labels are inverted to PhishX convention: 0 benign, 1 phishing. Only URLs and labels are imported. All 18 features are recomputed by PhishX.",
           '',f"The seeded sample contains {manifest['input_rows']:,} input rows. Cleaning retains {manifest['accepted_rows']:,}, removes {manifest['duplicates']} duplicates and {manifest['conflicting_urls_removed']} conflicting URLs, and rejects {len(manifest['rejected'])} invalid records.",
           '',f"The splitter joins registrable domains, supplied origin groups, and exact Unicode skeleton matches. Cross-partition canonical URL, actual domain, group and skeleton overlap counts: {manifest.get('overlap_audit',{})}.",
           '', '| Split | Rows | Benign | Phishing | Groups |','|---|---:|---:|---:|---:|']
    for name,split in manifest['splits'].items():
        lines.append(f"| {name} | {split['rows']} | {split['labels']['0']} | {split['labels']['1']} | {split.get('groups',split['domains'])} |")
    lines += ['',f"Random forest: 150 trees, selected max depth {evaluation['selected_max_depth']}, leaf minimum 2, balanced class weights, seed 42. Selection uses validation F1 only. Decision threshold is fixed at 0.5. Test rows do not select hyperparameters.",
              '', '## Held out results','', '| Measure | Random forest | Dummy baseline | HTTPS only diagnostic |','|---|---:|---:|---:|']
    for name in ('accuracy','precision','recall','f1','false_positive_rate','roc_auc','brier_score','log_loss'):
        results=[evaluation[key][name] for key in ('test','baseline','https_only_diagnostic')]
        lines.append('| '+name.replace('_',' ')+' | '+' | '.join(f'{v:.4f}' if v is not None else 'Unavailable' for v in results)+' |')
    lines += ['',f"Confusion matrix, rows actual benign/phishing and columns predicted benign/phishing: `{metrics['confusion_matrix']}`.",
              '', 'The HTTPS-only classifier is a source-bias diagnostic. If it performs well, those results do not establish robustness against phishing sites that use HTTPS.',
              '', '## Synthetic stress tests','', '| Family | Cases | Original recall on same cases | Variant recall | Lost detections |','|---|---:|---:|---:|---:|']
    for name,result in robustness['families'].items():
        if result['rows']:
            lines.append(f"| {name} | {result['rows']} | {result['paired_original_recall']:.4f} | {result['recall']:.4f} | {result['lost_detections']} |")
        else:lines.append(f'| {name} | 0 | Unavailable | Unavailable | Unavailable |')
    lines += ['',robustness['caveat'], '',
              'No generated family enters training or validation. Homoglyph is reserved from generation until frozen-model evaluation. This is an unseen generated-family check, not evidence that naturally occurring examples of the family were absent from the original dataset.',
              '', '## Probability and deployment limits','',
              'The artifact remains uncalibrated. Brier score, log loss, and reliability bins are diagnostic checks, not proof of calibration. The class-balanced historical sample does not reproduce real-world phishing prevalence. No probability-calibration mapping has been fitted.',
              '', 'The source was donated in 2024 and does not provide collection dates for individual rows. These results do not demonstrate present-day or temporal generalization. Subdomain changes and encoded paths are offline perturbations; altered homoglyph domains are hypothetical attack strings rather than verified live phishing URLs.',
              '',f"Unknown suffix rows: {manifest.get('unknown_suffix_rows','not audited')}. A zero count checks suffix coverage only; it does not validate labels or the full brand list.",
              '', '## Reproduction and handoff','',f"Model version: `{evaluation['model_version']}`.",
              '',f"Artifact SHA256: `{evaluation['artifact_sha256']}`.",
              '',f"Input CSV SHA256: `{manifest['input_sha256']}`.",
              '',f"UCI ZIP SHA256: `{source.get('downloaded_archive_sha256','not recorded')}`.",
              '', 'Local artifact: `artifacts/uci-run02/classical.joblib`. Full evaluation, probability bins, error cases and generated variants remain under ignored artifact directories. Reproduce them using `docs/person1-vscode.md`. Raw records and model binaries are not committed.',
              '', 'The classical detector does not implement the deep-model cascade, live domain signals, or deployment. This report alone does not establish the full 60 percent milestone.', '']
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text('\n'.join(lines))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('model_dir');p.add_argument('robustness_dir');p.add_argument('output')
    args=p.parse_args();write_report(args.model_dir,args.robustness_dir,args.output)
