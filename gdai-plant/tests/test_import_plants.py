import json
import sys
import tempfile
import unittest
from pathlib import Path
import sys

from pathlib import Path

INGESTION_DIR = Path(__file__).resolve().parents[1] / "ingestion"
sys.path.insert(0, str(INGESTION_DIR))

from import_plants import (
    normalize,
    parse_catalog,
    prepare,
    valid_horticultural_name,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ingestion'))
from import_plants import normalize, parse_catalog, verified_species, prepare


class ImportTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize('  Vinca  Minor '), 'vinca minor')

    def test_parse_and_duplicate_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'plants.json'
            f.write_text(json.dumps([{'scientific_name': 'Vinca minor'}]))
            self.assertEqual(len(parse_catalog(f)), 1)
            f.write_text(json.dumps([{'scientific_name': 'Vinca minor'}, {'scientific_name': 'vinca minor'}]))
            with self.assertRaises(ValueError):
                parse_catalog(f)

    def test_gbif_strict_match(self):
        row = {'normalized_scientific_name': 'vinca minor', 'gbif': {'matchType': 'EXACT', 'rank': 'SPECIES', 'status': 'ACCEPTED', 'canonicalName': 'Vinca minor'}}
        self.assertTrue(verified_species(row))
        row['gbif']['status'] = 'SYNONYM'
        self.assertFalse(verified_species(row))

    def test_dry_run(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'plants.json'
            f.write_text(json.dumps([{'scientific_name': 'Vinca minor'}]))
            result = prepare(f, online=False)
            self.assertEqual(result[0]['review_reason'], 'TAXONOMY_NOT_CHECKED')


    def test_horticultural_names(self):
        valid_names = [
            "Geranium macrorrhizum",
            "Vinca minor",
            "Prunus laurocerasus 'Otto Luyken'",
            "Cornus alba 'Sibirica'",
            "Pulmonaria 'Lewis Palmer'",
            "Sarcococca hookeriana var. humilis",
        ]

        for name in valid_names:
            with self.subTest(name=name):
                self.assertTrue(valid_horticultural_name(name))

        invalid_names = [
            "",
            "Pulmonaria",
            "Unknown plant name",
            "Vinca minor extra text",
        ]

        for name in invalid_names:
            with self.subTest(name=name):
                self.assertFalse(valid_horticultural_name(name))


if __name__ == '__main__':
    unittest.main()
