import copy
import importlib.util
import json
from pathlib import Path
import re
import unittest

import generate
from windows_catalog import validate

ROOT = Path(__file__).parent


class WindowsCatalogueTests(unittest.TestCase):
    def setUp(self):
        self.rows = json.loads((ROOT / 'data/windows-seed.json').read_text())
        self.record = copy.deepcopy(next(r for r in self.rows if r['name'] == 'VSCodium'))

    def test_seed(self):
        validate(self.rows)

    def test_identifier_cannot_be_a_link(self):
        self.record['alt_downloads'] = [{'label': 'winget', 'url': 'VSCodium.VSCodium'}]
        with self.assertRaisesRegex(ValueError, 'invalid download URL'):
            validate([self.record])

    def test_generic_platform_page_is_not_app_evidence(self):
        self.record['windows11'] = {'status': 'distributor', 'checked_at': '2026-10-12',
                                   'evidence_url': 'https://portableapps.com/download'}
        with self.assertRaisesRegex(ValueError, 'app-specific'):
            validate([self.record])

    def test_tested_claim_needs_environment(self):
        self.record['windows11'] = {'status': 'tested', 'tested': True, 'checked_at': '2026-10-12',
                                   'evidence_url': 'https://vscodium.com/'}
        with self.assertRaisesRegex(ValueError, 'test report'):
            validate([self.record])

    def test_duplicate_slug_rejected(self):
        second = copy.deepcopy(self.record)
        second['package'] = self.record['package'].replace('.', '-')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            validate([self.record, second])

    def test_winget_rendered_as_command(self):
        html = generate.windows_downloads(generate.clean_record(self.record))
        self.assertIn('<code>winget install --id VSCodium.VSCodium -e</code>', html)
        self.assertNotIn('href="VSCodium.VSCodium"', html)

    def test_generated_catalogue_and_pages_match_seed(self):
        apps = json.loads((ROOT / 'data/apps.json').read_text())
        windows = {a['package']: a for a in apps if a.get('platform') == 'windows'}
        sitemap = (ROOT / 'sitemap.xml').read_text()
        for row in self.rows:
            slug = generate.slugify(row['package'])
            path = ROOT / f'app/{slug}.html'
            if row['status'] not in ('include', 'per-badge', 'free-enough'):
                self.assertNotIn(row['package'], windows)
                self.assertFalse(path.exists(), slug)
                self.assertNotIn(f'/app/{slug}.html', sitemap)
                continue
            app = windows[row['package']]
            expected = generate.clean_record(row)
            self.assertEqual(app['downloads'], expected['downloads'])
            html = path.read_text()
            self.assertIn(generate.windows_downloads(app), html)
            self.assertIn(generate.windows_compatibility(app), html)
            self.assertIn(f'/app/{slug}.html', sitemap)


if __name__ == '__main__':
    unittest.main()
