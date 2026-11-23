import unittest
from matching.realistic_scenarios import validate, validate_batch

def sample(**changes):
    value = dict(id="G1", sun_exposure="FULL_SUN", soil_drainage="GOOD",
                 water_availability="LOW", minimum_winter_temperature_c=-8,
                 maximum_height_cm=250, maximum_spread_cm=150,
                 evergreen_preferred=True, origin="SYNTHETIC_AI",
                 plausibility_reason="A plausible temperate residential planting zone.")
    value.update(changes)
    return value

class ScenarioTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate(sample()).status, "ACCEPTED")
    def test_realistic_dry_clay_not_rejected(self):
        self.assertEqual(validate(sample(soil_drainage="POOR", water_availability="LOW")).status, "ACCEPTED")
    def test_contradiction(self):
        self.assertEqual(validate(sample(sun_exposure="FULL_SHADE", direct_sun_hours=8)).status, "REJECTED")
    def test_missing_observation_reference(self):
        self.assertEqual(validate(sample(origin="OBSERVED")).status, "REJECTED")
    def test_missing_explanation_requires_review(self):
        self.assertEqual(validate(sample(plausibility_reason="")).status, "REVIEW_REQUIRED")
    def test_duplicate_id(self):
        self.assertEqual(validate_batch([sample(), sample()])[1].status, "REJECTED")
    def test_duplicate_profile(self):
        self.assertEqual(validate_batch([sample(), sample(id="G2")])[1].status, "REVIEW_REQUIRED")
    def test_invalid_height(self):
        self.assertEqual(validate(sample(maximum_height_cm=-1)).status, "REJECTED")
    def test_boolean_temperature_invalid(self):
        self.assertEqual(validate(sample(minimum_winter_temperature_c=True)).status, "REJECTED")

if __name__ == "__main__":
    unittest.main()
