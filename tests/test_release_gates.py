"""Promotion must reject altered summaries and relaxed gates, without weights."""
import json
from pathlib import Path
import pytest
from phishx.release import validate_release_report

def report(version='v7'):
    return json.loads(Path(f'docs/evidence/completion/release-{version}.json').read_text())

def test_measured_passing_report_is_consistent():
    assert all(validate_release_report(report()).values())

def test_failed_report_cannot_be_promoted_by_flipping_boolean():
    failed=report('v6');failed['all_quality_gates_passed']=True
    failed['quality_checks']={k:True for k in failed['quality_checks']}
    with pytest.raises(ValueError,match='quality gates'):validate_release_report(failed)

def test_altered_rates_and_relaxed_gates_rejected():
    altered=report();altered['cohorts']['fresh_external']['cascade']['false_positive_rate']=0.
    with pytest.raises(ValueError,match='confusion counts'):validate_release_report(altered)
    altered=report();altered['quality_gates']['external_max_false_positive_rate']=.10
    with pytest.raises(ValueError,match='registered plan'):validate_release_report(altered)
