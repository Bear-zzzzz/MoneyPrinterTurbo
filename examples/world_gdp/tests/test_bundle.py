import hashlib
import json
import unittest
from pathlib import Path

from paths import PACKAGE, DATA, ASSETS, OUTPUT, PROJECT, REFERENCES


class BundleTests(unittest.TestCase):
    def test_paths_stay_in_package_without_original_storage(self):
        self.assertEqual(DATA, PACKAGE / 'data')
        self.assertEqual(ASSETS, PACKAGE / 'assets')
        self.assertEqual(OUTPUT, PACKAGE / 'output')
        self.assertTrue((PROJECT / 'resource/fonts/STHeitiMedium.ttc').is_file())

    def test_asset_manifest_has_license_and_local_hashes(self):
        manifest = json.loads((REFERENCES / 'stock-inputs.json').read_text())
        self.assertEqual([entry['id'] for entry in manifest['assets']], [3759, 52302])
        for entry in manifest['assets']:
            self.assertTrue(entry['local_only'])
            self.assertFalse(entry['original_has_alpha'])
            self.assertEqual(len(entry['sha256']), 64)
            self.assertTrue(entry['license_page'].startswith('https://mixkit.co/'))
            path = ASSETS / 'local-only' / entry['filename']
            if path.is_file():
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry['sha256'])

    def test_composite_source_has_no_hardcoded_home_directory(self):
        for path in (PACKAGE / 'scripts').glob('*.py'):
            self.assertNotIn('/Users/' + 'xiongwei8', path.read_text())


if __name__ == '__main__':
    unittest.main()
