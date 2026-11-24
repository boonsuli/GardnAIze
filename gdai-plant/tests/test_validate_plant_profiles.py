import unittest
from jsonschema import ValidationError
from enrichment.prepare_profile_pilot import TRAITS
from enrichment.validate_plant_profiles import validate

class ValidationTest(unittest.TestCase):
    def setUp(self):
        self.payload = {"profiles": [{"scientific_name": "Plant A", "traits": {
            k: {"value": None, "source_urls": [], "notes": "Unknown", "evidence_status": "UNKNOWN"} for k in TRAITS}}]}
        self.traits = self.payload["profiles"][0]["traits"]

    def test_unknown_allowed(self):
        self.assertEqual(validate(self.payload, ["Plant A"])["profiles"], 1)

    def test_wrong_name(self):
        with self.assertRaises(ValueError):
            validate(self.payload, ["Plant B"])

    def test_unsupported_value(self):
        self.traits["evergreen"]["value"] = True
        self.assertTrue(validate(self.payload, ["Plant A"])["warnings"])

    def test_catalogue_listing(self):
        self.traits["french_nursery_availability"].update(value="LISTED", evidence_status="SUGGESTED")
        self.assertEqual(validate(self.payload, ["Plant A"])["status"], "STRUCTURE_VALID_PENDING_REVIEW")

    def test_invalid_enum(self):
        self.traits["sun_exposure"]["value"] = ["SUN"]
        with self.assertRaises(ValidationError):
            validate(self.payload, ["Plant A"])

    def test_reversed_range(self):
        self.traits["height_cm"].update(value=[300, 100], source_urls=["https://example.org/plant"], evidence_status="RETRIEVED")
        with self.assertRaises(ValueError):
            validate(self.payload, ["Plant A"])
