import unittest
from enrichment.generate_gemini_profiles import extract

class GeminiExtractionTest(unittest.TestCase):
    def test_grounded(self):
        response = {"candidates": [{"finishReason": "STOP", "groundingMetadata": {"groundingChunks": [{}]}, "content": {"parts": [{"text": '{"profiles": []}'}]}}]}
        self.assertEqual(extract(response), {"profiles": []})

    def test_missing_grounding(self):
        response = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": '```json\n{"profiles": []}\n```'}]}}]}
        self.assertEqual(extract(response), {"profiles": []})

    def test_truncated(self):
        with self.assertRaises(ValueError):
            extract({"candidates": [{"finishReason": "MAX_TOKENS"}]})
