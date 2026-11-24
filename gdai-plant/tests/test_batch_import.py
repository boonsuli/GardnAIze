import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ingestion'))
from import_batch import chunks, run

class BatchImportTests(unittest.TestCase):
    def test_chunks(self):
        self.assertEqual([len(x) for x in chunks(list(range(65)), 30)], [30, 30, 5])

    def test_bad_batch_size(self):
        with self.assertRaises(ValueError):
            list(chunks([1], 0))

    def test_duplicate_across_batches(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'plants.json'
            p.write_text(json.dumps([{'scientific_name': 'Vinca minor'}, {'scientific_name': 'Vinca minor'}]))
            with self.assertRaises(ValueError):
                run(p, Path(d) / 'out.ndjson', batch_size=1)

    def test_offline_dry_run(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'plants.json'
            p.write_text(json.dumps([{'scientific_name': 'Vinca minor'}, {'scientific_name': 'Geranium macrorrhizum'}]))
            with patch('import_batch.write_db') as write:
                summary = run(p, Path(d) / 'out.ndjson', batch_size=1)
                write.assert_not_called()
            self.assertEqual(summary['batches'], 2)
            self.assertEqual(summary['processed'], 2)
            self.assertEqual(len((Path(d) / 'out.ndjson').read_text().splitlines()), 2)

if __name__ == '__main__':
    unittest.main()
