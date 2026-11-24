import unittest
from enrichment.prepare_profile_pilot import prepare, TRAITS

class PilotTest(unittest.TestCase):
    def test_prompt(self):
        plants = [{"scientific_name": f"Plant {i}"} for i in range(6)]
        prompt = prepare(plants, "GardnAIze", 0, 5)
        self.assertIn("Plant 4", prompt)
        self.assertNotIn("Plant 5", prompt)
        for trait in TRAITS:
            self.assertIn(trait, prompt)

    def test_invalid_batch(self):
        with self.assertRaises(ValueError):
            prepare([], "", 0, 6)
