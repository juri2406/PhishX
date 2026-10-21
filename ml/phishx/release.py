"""Recompute registered promotion gates from measured confusion counts."""
REGISTERED_GATES={
 'external_max_false_positive_rate':.05,
 'each_holdout_max_recall_drop_against_rf':.02,
 'uci_min_recall':.90,'uci_max_false_positive_rate':.05,'external_min_recall':.88,
}

def validate_release_report(report):
    if not report.get('all_quality_gates_passed'):
        raise ValueError('Release candidate did not pass its registered quality gates')
    if report.get('quality_gates')!=REGISTERED_GATES:
        raise ValueError('Release quality gates differ from the registered plan')
    rates={}
    for name in ('fresh_uci','fresh_external'):
        rates[name]={}
        for model in ('classical','cascade'):
            metrics=report['cohorts'][name][model]
            (tn,fp),(fn,tp)=metrics['confusion_matrix']
            if any(type(n) is not int or n<0 for n in (tn,fp,fn,tp)) or not tn+fp or not fn+tp:
                raise ValueError('Invalid release confusion counts')
            recall=tp/(tp+fn);fpr=fp/(tn+fp)
            if sum((tn,fp,fn,tp))!=metrics['rows'] or abs(recall-metrics['recall'])>1e-12 or abs(fpr-metrics['false_positive_rate'])>1e-12:
                raise ValueError('Release metrics disagree with measured confusion counts')
            rates[name][model]=(recall,fpr)
    u,e=rates['fresh_uci'],rates['fresh_external']
    checks={'uci_recall':u['cascade'][0]>=.90,'uci_fpr':u['cascade'][1]<=.05,
            'external_recall':e['cascade'][0]>=.88,'external_fpr':e['cascade'][1]<=.05,
            'recall_noninferiority':all(r['cascade'][0]>=r['classical'][0]-.02 for r in rates.values()),
            'fpr_did_not_worsen':all(r['cascade'][1]<=r['classical'][1] for r in rates.values())}
    if report.get('quality_checks')!=checks or not all(checks.values()):
        raise ValueError('Measured release quality gates failed or their summary was altered')
    return checks
