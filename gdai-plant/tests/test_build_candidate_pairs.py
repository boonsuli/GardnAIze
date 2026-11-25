import json
import unittest
from collections import Counter
from matching.build_candidate_pairs import ROOT, build

class CandidatePairsTest(unittest.TestCase):
    def setUp(self):
        self.gardens = json.loads((ROOT / "data/scenarios/garden-scenarios-final-v2.json").read_text(encoding="utf-8"))["scenarios"]
        self.plants = json.loads((ROOT / "data/plants-mvp-40.json").read_text(encoding="utf-8"))

    def test_complete_unique_unlabelled(self):
        rows = build(self.gardens, self.plants)
        self.assertEqual(len(rows), 2000)
        self.assertEqual(len({(r["garden_id"], r["scientific_name"]) for r in rows}), 2000)
        self.assertEqual(set(Counter(r["garden_id"] for r in rows).values()), {40})
        self.assertEqual(set(Counter(r["scientific_name"] for r in rows).values()), {50})
        self.assertTrue(all(r["relevance_grade"] is None and r["label_source"] is None and r["assessment_status"] == "PENDING" for r in rows))
        self.assertEqual(rows, build(self.gardens, self.plants))

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            build(self.gardens, self.plants[:-1] + self.plants[:1])

    def test_missing_garden_rejected(self):
        with self.assertRaises(ValueError):
            build(self.gardens[:-1], self.plants)
