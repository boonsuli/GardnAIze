import copy
import unittest

from matching.finalize_garden_scenarios import finalize


def sample(sid):
    return {
        "id": sid, "sun_exposure": "FULL_SUN", "soil_drainage": "MODERATE",
        "water_availability": "MEDIUM", "minimum_winter_temperature_c": -8,
        "maximum_height_cm": 200, "maximum_spread_cm": 150,
        "evergreen_preferred": False, "origin": "SYNTHETIC_AI",
        "plausibility_reason": "Temperate lowland garden.",
        "climate_zone": "TEMPERATE_TRANSITIONAL", "soil_texture": "LOAM",
        "soil_moisture_seasonality": "WELL_DRAINED",
        "planting_context": "IN_GROUND_BORDER", "terrain_type": "LOWLAND",
    }


class FinalV2Tests(unittest.TestCase):
    def test_rejects_wrong_raw_count(self):
        with self.assertRaisesRegex(ValueError, "Expected 53"):
            finalize({"records": [{"scenario": sample("A")}]}, {"reviews": []})

    def test_rejects_duplicate_ids(self):
        a = sample("A")
        with self.assertRaisesRegex(ValueError, "Duplicate IDs"):
            finalize({"records": [{"scenario": a}]},
                     {"reviews": [{"scenario": copy.deepcopy(a)}]})

    def test_rejects_unexpected_unreviewed_similarity(self):
        # Integration tests with actual 53 input records are run by CLI.
        from matching.consolidate_garden_scenarios import near_duplicate_pairs
        a, b = sample("A"), sample("B")
        self.assertEqual(len(near_duplicate_pairs([a, b])), 1)


if __name__ == "__main__":
    unittest.main()
