import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'build_mvp40.py'
spec = importlib.util.spec_from_file_location('build_mvp40', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class MVP40Tests(unittest.TestCase):
    def test_count_and_diversity(self):
        self.assertEqual(sum(map(len, mod.GROUPS.values())), 40)
        self.assertEqual(len(mod.GROUPS), 6)
        self.assertEqual(len(set(x.casefold() for a in mod.GROUPS.values() for x in a)), 40)

    def test_blank_traits_and_status(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(mod, 'DATA', Path(tmp)):
            jp, cp = mod.build()
            self.assertEqual(len(json.loads(jp.read_text())), 40)
            with cp.open(newline='', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 40)
            self.assertTrue(all(r['quality_status'] == 'PENDING' for r in rows))
            self.assertTrue(all(not r['sun_exposure'] and not r['hardiness_min_c']
                                and not r['nursery_product_url'] for r in rows))

    def test_no_overwrite_of_enriched_data(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(mod, 'DATA', Path(tmp)):
            _, cp = mod.build()
            with self.assertRaises(FileExistsError):
                mod.build()

if __name__ == '__main__':
    unittest.main()
