import unittest
from matching.enrich_pilot_scenarios import enrich, ENRICHMENT, EXCLUDED

def fixture():
    return {"schema_version": "1.2", "reviews": [
        {"scenario": {
            "id": sid, "sun_exposure": "FULL_SUN", "soil_drainage": "GOOD",
            "water_availability": "MEDIUM", "minimum_winter_temperature_c": -8,
            "maximum_height_cm": 200, "maximum_spread_cm": 150,
            "evergreen_preferred": False, "origin": "SYNTHETIC_AI",
            "plausibility_reason": "Synthetic residential garden planting zone.",
        }} for sid in list(ENRICHMENT) + list(EXCLUDED)
    ]}

class EnrichmentTests(unittest.TestCase):
    def test_nine_enriched_and_jura_excluded(self):
        data = fixture()
        result = enrich(data)
        self.assertEqual(len(result["reviews"]), 9)
        self.assertEqual(result["excluded"][0]["id"], "FR-JUR-10")
        self.assertEqual(result["summary"]["ACCEPTED"], 9)
        self.assertNotIn("climate_zone", data["reviews"][0]["scenario"])
    def test_unknown_id_refused(self):
        data = fixture()
        data["reviews"][0]["scenario"]["id"] = "UNKNOWN"
        with self.assertRaises(ValueError):
            enrich(data)
    def test_duplicate_id_refused(self):
        data = fixture()
        data["reviews"][1]["scenario"]["id"] = "FR-PAR-01"
        with self.assertRaises(ValueError):
            enrich(data)
    def test_missing_scenario_refused(self):
        data = fixture()
        data["reviews"].pop()
        with self.assertRaises(ValueError):
            enrich(data)

if __name__ == "__main__":
    unittest.main()
