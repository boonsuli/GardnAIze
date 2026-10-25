import base64
import os
import unittest
from unittest.mock import patch

from app.garden_analysis import analyze_image


class GardenAnalysisTests(unittest.TestCase):
    def test_unsupported_media_type(self):
        with self.assertRaises(ValueError):
            analyze_image(base64.b64encode(b"image").decode(), "image/webp")

    def test_invalid_base64(self):
        with self.assertRaises(ValueError):
            analyze_image("not base64!", "image/jpeg")

    def test_missing_key(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            with self.assertRaises(RuntimeError):
                analyze_image(base64.b64encode(b"test").decode(), "image/jpeg")


if __name__ == "__main__":
    unittest.main()
