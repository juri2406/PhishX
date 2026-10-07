"""Compare live HTTP model output to trusted standalone inference.

Run from the repository root with PYTHONPATH=ml:. (ml;. on Windows).
This is application acceptance, not a new accuracy or robustness benchmark.
"""
import argparse
import csv
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path

from ml.integration import ModelProvider


def request(api, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(api.rstrip('/') + path, data=data,
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, json.load(exc)


def verify(api, model, output, test_csv=None):
    provider = ModelProvider(model)
    status, health = request(api, '/health')
    assert status == 200 and health['ready'] and health['mode'] == 'model'
    assert health['model_version'] == provider.version
    cases = []
    if test_csv:
        with Path(test_csv).open(encoding='utf-8', newline='') as file:
            rows = list(csv.DictReader(file))
        for label in ('0', '1'):
            selected = [row for row in rows if row['label'] == label][:6]
            assert len(selected) == 6, 'Need six held-out rows per class'
            cases.extend((f'uci-{label}-{i+1}', row['url'])
                         for i, row in enumerate(selected))
    else:
        cases.extend([('official-domain', 'https://github.com/'),
                      ('official-brand', 'https://paypal.com/')])
    cases.extend((f'synthetic-{i+1}', url) for i, url in enumerate([
        'https://pаypal.com/login', 'https://раypal.example/login',
        'https://gіthub.example', 'https://micrоsoft.example']))
    checks = []
    for case_id, url in cases:
        status, actual = request(api, '/scan', {'url': url})
        assert status == 200 and actual['mode'] == 'model'
        prediction = provider.predict(url)
        explanation = provider.explain(prediction)
        expected = sorted(explanation.items, key=lambda item: item.contribution,
                          reverse=True)[:3]
        assert actual['model_version'] == provider.version
        assert actual['normalized_host'] == prediction.normalized_host
        assert abs(actual['phishing_probability'] - prediction.phishing_probability) < 1e-12
        assert actual['explanation_status'] == 'available'
        assert actual['explanation_scale'] == explanation.scale
        assert len(actual['explanation_items']) == len(expected)
        for item, standalone in zip(actual['explanation_items'], expected):
            assert item['feature'] == standalone.feature
            assert item['observed_value'] == standalone.observed_value
            assert abs(item['contribution'] - standalone.contribution) < 1e-12
        checks.append({'id': case_id, 'risk_score': actual['risk_score'],
                       'standalone_match': True, 'shap_match': True})
    for i, url in enumerate(['ftp://example.com', 'https://x..com',
                             'https://example.com/%zz', 'https://exa mple.com']):
        status, actual = request(api, '/scan', {'url': url})
        assert status == 422 and actual['error']['message']
        checks.append({'id': f'invalid-{i+1}', 'status': status,
                       'error_code': actual['error']['code']})
    report = {'model_version': provider.version,
              'model_sha256': hashlib.sha256(Path(model).read_bytes()).hexdigest(),
              'scope': 'Live localhost HTTP versus standalone inference; no page visits',
              'checks': checks}
    if test_csv:
        report['test_csv_sha256'] = hashlib.sha256(Path(test_csv).read_bytes()).hexdigest()
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'Passed {len(checks)} HTTP acceptance cases; saved {target}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api', default='http://127.0.0.1:8000')
    parser.add_argument('--model', default='artifacts/uci-run03/classical.joblib')
    parser.add_argument('--test-csv')
    parser.add_argument('--output', default='work/application-acceptance.json')
    args = parser.parse_args()
    verify(args.api, args.model, args.output, args.test_csv)
