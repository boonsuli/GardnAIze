import unittest
from matching.consolidate_garden_scenarios import consolidate, near_duplicate_pairs

def scenario(sid):
    return {"id": sid, "sun_exposure": "FULL_SUN", "soil_drainage": "MODERATE",
            "water_availability": "MEDIUM", "minimum_winter_temperature_c": -8,
            "maximum_height_cm": 200, "maximum_spread_cm": 150,
            "evergreen_preferred": False, "origin": "SYNTHETIC_AI",
            "plausibility_reason": "Residential garden planting zone.",
            "climate_zone": "TEMPERATE_TRANSITIONAL", "soil_texture": "LOAM",
            "soil_moisture_seasonality": "WELL_DRAINED",
            "planting_context": "IN_GROUND_BORDER", "terrain_type": "LOWLAND"}

class ConsolidationTests(unittest.TestCase):
    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            consolidate([scenario("A")], [scenario("A")])
    def test_near_duplicate_detected(self):
        a, b = scenario("A"), scenario("B")
        b["minimum_winter_temperature_c"] = -7
        self.assertEqual(len(near_duplicate_pairs([a, b])), 1)
    def test_manual_exclusion_is_explicit(self):
        result = consolidate([scenario("FR-PAR-01")], [scenario("FR-TEM-001")])
        record = next(r for r in result["records"] if r["id"] == "FR-TEM-001")
        self.assertEqual(record["decision"], "EXCLUDED_NEAR_DUPLICATE")
        self.assertEqual(result["total_input"], 2)
    def test_ambiguous_context_requires_review(self):
        result = consolidate([], [scenario("FR-TEM-019")])
        self.assertEqual(result["records"][0]["decision"], "MANUAL_REVIEW_REQUIRED")
    def test_no_mutation(self):
        first = [scenario("A")]
        consolidate(first, [scenario("B")])
        self.assertNotIn("decision", first[0])

if __name__ == "__main__":
    unittest.main()
