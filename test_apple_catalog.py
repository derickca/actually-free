import copy
import json
from pathlib import Path
import unittest

import generate
from apple_catalog import validate_macos, validate_ios

ROOT = Path(__file__).parent

MAC_RECORD = {
    "name": "Example Player", "package": "org.example.player",
    "platform": "macos", "category": "Media", "subcategory": "Video",
    "official_url": "https://example.org/player/",
    "alt_downloads": [{"label": "Mac App Store",
                       "url": "https://apps.apple.com/ca/app/example-player/id123456789"}],
    "stores": {"appstore": "https://apps.apple.com/ca/app/example-player/id123456789"},
    "brew_id": "example-player",
    "description": "Plays videos.", "status": "include",
    "verification": {"method": "official-site",
                     "evidence_url": "https://example.org/player/",
                     "checked_at": "2026-10-16"},
}

IOS_RECORD = {
    "name": "Example Notes", "package": "org.example.notes",
    "platform": "ios", "category": "Productivity", "subcategory": "Notes",
    "stores": {"appstore": "https://apps.apple.com/ca/app/example-notes/id987654321"},
    "description": "Takes notes.", "status": "include",
    "verification": {"method": "appstore", "iap_free": True,
                     "no_ads_declared": True, "privacy": "Data Not Collected",
                     "appstore_rating": 4.8,
                     "evidence_url": "https://apps.apple.com/ca/app/example-notes/id987654321",
                     "checked_at": "2026-10-16"},
}


class AppleCatalogueTests(unittest.TestCase):
    def setUp(self):
        self.mac = copy.deepcopy(MAC_RECORD)
        self.ios = copy.deepcopy(IOS_RECORD)
        self.mac_seed = json.loads((ROOT / 'data/macos-seed.json').read_text())
        self.ios_seed = json.loads((ROOT / 'data/ios-seed.json').read_text())

    def test_seed_files_validate(self):
        validate_macos(self.mac_seed)
        validate_ios(self.ios_seed)

    def test_macos_wrong_platform_rejected(self):
        self.mac['platform'] = 'windows'
        with self.assertRaisesRegex(ValueError, 'platform must be macos'):
            validate_macos([self.mac])

    def test_macos_appstore_alt_must_be_appstore(self):
        self.mac['alt_downloads'] = [{"label": "Mac App Store",
                                      "url": "https://example.org/store"}]
        with self.assertRaisesRegex(ValueError, 'Mac App Store'):
            validate_macos([self.mac])

    def test_macos_needs_a_download_path(self):
        self.mac['official_url'] = None
        self.mac['alt_downloads'] = []
        self.mac['stores'] = {}
        with self.assertRaisesRegex(ValueError, 'download path'):
            validate_macos([self.mac])

    def test_macos_evidence_required(self):
        del self.mac['verification']['evidence_url']
        with self.assertRaisesRegex(ValueError, 'evidence_url'):
            validate_macos([self.mac])

    def test_ios_include_requires_iap_free(self):
        self.ios['verification']['iap_free'] = False
        with self.assertRaisesRegex(ValueError, 'iap_free'):
            validate_ios([self.ios])

    def test_ios_include_requires_no_ads_declared(self):
        self.ios['verification']['no_ads_declared'] = False
        with self.assertRaisesRegex(ValueError, 'no_ads_declared'):
            validate_ios([self.ios])

    def test_ios_appstore_url_needs_numeric_id(self):
        self.ios['stores']['appstore'] = 'https://apps.apple.com/ca/app/example-notes/'
        self.ios['verification']['evidence_url'] = self.ios['stores']['appstore']
        with self.assertRaisesRegex(ValueError, 'numeric app id'):
            validate_ios([self.ios])

    def test_duplicate_slug_rejected(self):
        second = copy.deepcopy(self.mac)
        second['package'] = self.mac['package'].replace('.', '-')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            validate_macos([self.mac, second])

    def test_brew_rendered_as_command(self):
        html = generate.macos_downloads(generate.clean_record(self.mac))
        self.assertIn('<code>brew install --cask example-player</code>', html)
        self.assertIn('Download from the developer', html)
        self.assertIn('Mac App Store', html)

    def test_ios_detail_uses_appstore_badge_and_rating_source(self):
        html = generate.build_detail(generate.clean_record(self.ios),
                                     generate.FeedbackForms())
        self.assertIn('App Store', html)
        self.assertIn('on the App Store', html)
        self.assertIn('iOS', html)

    def test_macos_detail_renders(self):
        html = generate.build_detail(generate.clean_record(self.mac),
                                     generate.FeedbackForms())
        self.assertIn('Mac', html)
        self.assertIn('brew install --cask example-player', html)


if __name__ == '__main__':
    unittest.main()
