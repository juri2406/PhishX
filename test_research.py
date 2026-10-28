import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from scripts.import_uci import import_uci
from phishx.robustness import variant
from phishx.model import probability_report
from phishx.dataset import prepare
from phishx.skeleton import skeleton
from phishx.urls import normalize_url
from urllib.parse import unquote,urlsplit

class ResearchTests(unittest.TestCase):
    def test_uci_label_direction_and_sampling(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); archive=root/'dataset.zip'
            with ZipFile(archive,'w') as z:
                z.writestr('test.csv','URL,label,Unused\n'+''.join(f'https://domain{i}.com,{i%2},999\n' for i in range(30)))
            a=import_uci(archive,root/'a.csv',5)
            b=import_uci(archive,root/'b.csv',5)
            self.assertEqual((root/'a.csv').read_bytes(),(root/'b.csv').read_bytes())
            with (root/'a.csv').open() as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),10)
            for row in rows:
                index=int(row['url'].split('domain')[1].split('.')[0])
                self.assertEqual(int(row['label']),1-index%2)
                self.assertEqual(row['collected_at'],'unknown')
                self.assertNotIn('Unused',row)
            self.assertEqual(a['license'],'CC BY 4.0')
            excluded=root/'excluded.csv'
            excluded.write_text('url,label,source,collected_at\nhttps://domain0.com/,1,fixture,unknown\n')
            new=import_uci(archive,root/'c.csv',5,42,excluded)
            self.assertEqual(new['excluded_prior_rows'],1)
            with (root/'c.csv').open() as f:
                self.assertTrue(all('domain0.com' not in r['url'] for r in csv.DictReader(f)))

    def test_variants_preserve_intended_components(self):
        original='https://account-example.com/login?next=home'
        encoded=variant(original,'percent_encoding')
        self.assertEqual(unquote(urlsplit(encoded).path),urlsplit(original).path)
        self.assertEqual(urlsplit(encoded).query,'next=home')
        deceptive=variant(original,'subdomain')
        self.assertEqual(normalize_url(deceptive).registrable_domain,normalize_url(original).registrable_domain)
        homoglyph=variant(original,'homoglyph')
        self.assertNotEqual(normalize_url(homoglyph).ascii_host,normalize_url(original).ascii_host)
        self.assertEqual(skeleton(normalize_url(homoglyph).unicode_host),skeleton(normalize_url(original).unicode_host))
        self.assertIsNone(variant('https://example.com/','percent_encoding'))
        self.assertIsNone(variant('https://127.0.0.1/login','homoglyph'))

    def test_probability_diagnostics(self):
        report=probability_report([0,1,0,1],[0.1,0.9,0.2,0.8])
        self.assertEqual(report['confusion_matrix'],[[2,0],[0,2]])
        self.assertAlmostEqual(report['brier_score'],.025)
        self.assertEqual(sum(b['count'] for b in report['probability_bins']),4)

    def test_connected_skeleton_groups(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); path=root/'input.csv'
            rows=[dict(url=f'https://domain{i}.com/',label=str(i%2),source='fixture',collected_at='unknown',group_domain='',family='original') for i in range(80)]
            rows += [dict(url='https://paypal.com/a',label='0',source='fixture',collected_at='unknown',group_domain='',family='original'),
                     dict(url='https://pаypal.com/a',label='1',source='fixture',collected_at='unknown',group_domain='',family='original'),
                     dict(url='https://paypal.com/b',label='0',source='fixture',collected_at='unknown',group_domain='other.com',family='fixture')]
            with path.open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
            manifest=prepare(path,root/'splits')
            locations=[]
            for name in ('train','validation','test'):
                with (root/'splits'/f'{name}.csv').open() as f:
                    subset=list(csv.DictReader(f))
                if any('paypal.com/' in r['url'] or 'pаypal.com/' in r['url'] for r in subset):locations.append(name)
            self.assertEqual(len(locations),1)
            self.assertTrue(all(n==0 for n in manifest['overlap_audit'].values()))
