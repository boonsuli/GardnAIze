import unittest
from enrichment.prepare_profile_pilot import TRAITS
from enrichment.prepare_claude_review import digest, prepare
from enrichment.validate_claude_review import validate_review
from enrichment.consolidate_plant_profiles import consolidate

class ClaudePipelineTest(unittest.TestCase):
    def setUp(self):
        self.g = {"profiles": [{"scientific_name": "Plant A", "traits": {
            k: {"value": None, "source_urls": [], "notes": "Unknown", "evidence_status": "UNKNOWN"} for k in TRAITS}}]}
        self.g["profiles"][0]["traits"]["evergreen"]["value"] = True
        self.r = {"input_sha256": digest(self.g), "profiles": [{"scientific_name": "Plant A", "traits": {
            k: {"verdict": "UNCERTAIN", "proposed_value": None, "source_urls": [], "justification": "Unknown"} for k in TRAITS}}]}
        self.r["profiles"][0]["traits"]["evergreen"].update(verdict="SUPPORTED", proposed_value=True)

    def test_prompt(self):
        self.assertIn(digest(self.g), prepare(self.g, ["Plant A"]))

    def test_consensus(self):
        result, report = consolidate(self.g, self.r)
        self.assertIs(result["profiles"][0]["traits"]["evergreen"]["value"], True)
        self.assertEqual(report["retained_traits"], 1)

    def test_disagreement(self):
        self.r["profiles"][0]["traits"]["evergreen"].update(verdict="CONTRADICTED", proposed_value=False)
        result, _ = consolidate(self.g, self.r)
        self.assertIsNone(result["profiles"][0]["traits"]["evergreen"]["value"])

    def test_digest_mismatch(self):
        self.r["input_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            validate_review(self.g, self.r)

    def test_false_agreement(self):
        self.r["profiles"][0]["traits"]["evergreen"]["proposed_value"] = False
        with self.assertRaises(ValueError):
            validate_review(self.g, self.r)
