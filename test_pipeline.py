import csv
import tempfile
import unittest
from pathlib import Path
from phishx import analyze_url, normalize_url, InvalidURL, FEATURE_NAMES
from phishx.skeleton import skeleton
from phishx.dataset import prepare

class URLTests(unittest.TestCase):
    def test_unicode_punycode_equivalence(self):
        u=normalize_url('https://pаypal.com')
        self.assertEqual(u.ascii_host,'xn--pypal-4ve.com')
        self.assertEqual(u.canonical,normalize_url('https://'+u.ascii_host).canonical)
        a=analyze_url('https://pаypal.com')
        self.assertEqual(a['brand_match']['closest_brand'],'paypal')
        self.assertEqual(a['brand_match']['distance'],0)
        self.assertEqual(a['features']['confusable_non_ascii'],1)
    def test_legitimate_domain_and_path(self):
        for url in ('https://paypal.com','https://www.paypal.com/login'):
            self.assertFalse(analyze_url(url)['brand_match']['impersonation_signal'])
        self.assertFalse(analyze_url('https://example.org/paypal')['brand_match']['impersonation_signal'])
    def test_subdomain_and_suffix(self):
        a=analyze_url('https://paypal.attacker.co.uk')
        self.assertEqual(a['normalized']['registrable_domain'],'attacker.co.uk')
        self.assertEqual(a['features']['brand_in_subdomain'],1)
        self.assertEqual(normalize_url('https://alice.github.io').registrable_domain,'alice.github.io')
    def test_private_suffix_host_itself(self):
        for host in ('github.io','s3.amazonaws.com','cloudflare-ipfs.com'):
            with self.subTest(host=host):
                self.assertEqual(normalize_url('https://'+host+'/content').registrable_domain,host)

    def test_formatting_equivalent_features(self):
        variants=['https://paypal.com','https://paypal.com/','https://www.paypal.com','https://www.paypal.com/']
        features=[analyze_url(u)['features'] for u in variants]
        self.assertTrue(all(row==features[0] for row in features))

    def test_invalid(self):
        for url in ('', 'javascript:alert(1)','ftp://example.org','https://x..com','https://example.org:99999','https://example.org/a b','https://example.org/%zz','https://exa\\mple.org'):
            with self.subTest(url=url),self.assertRaises(InvalidURL): normalize_url(url)
    def test_preserve_indicators(self):
        a=analyze_url('https://paypal.com@attacker.org/%61')
        self.assertEqual(a['normalized']['ascii_host'],'attacker.org')
        self.assertEqual(a['features']['userinfo_present'],1)
        self.assertEqual(a['features']['percent_encoding_present'],1)
        self.assertEqual(analyze_url('example.org')['features']['https_explicit'],0)
    def test_ip_and_schema(self):
        self.assertTrue(normalize_url('http://[::1]/').is_ip)
        self.assertEqual(tuple(analyze_url('https://example.org')['features']),FEATURE_NAMES)
        self.assertEqual(skeleton('pаypal'),skeleton('paypal'))

class DataTests(unittest.TestCase):
    def test_grouping_duplicates_conflicts_and_training(self):
        from phishx.model import train,predict
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'input.csv'
            fields=['url','label','source','collected_at','group_domain','family']
            rows=[]
            for i in range(100):
                for label in (0,1):
                    domain=f"{'benign' if label==0 else 'phishing'}{i}.com"
                    for path in ('a','b'):
                        rows.append(dict(url=f'https://{domain}/{path}',label=str(label),source='synthetic-test-only',collected_at='2026-10-06',group_domain=domain,family='fixture'))
            rows += [rows[0].copy(),dict(rows[1],label='1'),dict(rows[2],url='invalid')]
            with source.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
            manifest=prepare(source,root/'splits')
            self.assertEqual(manifest['duplicates'],1)
            self.assertEqual(manifest['conflicting_urls_removed'],1)
            self.assertEqual(len(manifest['rejected']),1)
            seen=[]
            for name in ('train','validation','test'):
                with (root/'splits'/f'{name}.csv').open() as f: records=list(csv.DictReader(f))
                seen.append({r['group_domain'] for r in records})
                self.assertFalse(any(r['canonical']==normalize_url(rows[1]['url']).canonical for r in records))
            self.assertFalse(seen[0]&seen[1] or seen[1]&seen[2] or seen[0]&seen[2])
            report=train(root/'splits',root/'model')
            self.assertIn('confusion_matrix',report['test'])
            result=predict('https://example.org',root/'model'/'classical.joblib')
            self.assertGreaterEqual(result['risk_score'],0);self.assertLessEqual(result['risk_score'],100)
            self.assertEqual(result['cascade_status'],'not_implemented')
            with self.assertRaises(ValueError): prepare(source,root/'splits')

if __name__=='__main__': unittest.main()
