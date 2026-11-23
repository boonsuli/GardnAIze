import base64
import io
import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from app.garden_analysis import analyze_image


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return io.BytesIO(json.dumps(self.payload).encode())

    def __exit__(self, *args):
        return False


class GardenAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.image = base64.b64encode(b"RIFF1234WEBPVP8 ").decode()
        self.analysis = {
            "isGarden": True, "isAnalyzable": True, "climateCode": "TEMPERATE",
            "description": {
                "summary": "Lawn and terrace",
                "features": {"lawn": True, "terrace": True, "pathway": False,
                             "trees": False, "shrubs": True, "fence": True,
                             "lowWall": False, "stairs": False, "slope": False}
            }
        }

    def test_unsupported_media_type(self):
        with self.assertRaises(ValueError):
            analyze_image(self.image, "image/gif")

    def test_invalid_base64(self):
        with self.assertRaises(ValueError):
            analyze_image("not base64!", "image/webp")

    @patch.dict(os.environ, {"GEMINI_API_KEY": ""})
    def test_missing_key(self):
        with self.assertRaises(RuntimeError):
            analyze_image(self.image, "image/webp")

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-secret", "GEMINI_MODEL": "test-model"})
    @patch("app.garden_analysis.request.urlopen")
    def test_webp_payload_and_observations(self, urlopen):
        provider = {"candidates": [{"content": {"parts": [{"text": json.dumps(self.analysis)}]}}]}
        urlopen.return_value = FakeResponse(provider)
        result = analyze_image(self.image, "image/webp")
        self.assertEqual("UNKNOWN", result["climateCode"])
        self.assertEqual("1.0", result["schemaVersion"])
        self.assertTrue(result["description"]["features"]["terrace"])
        sent = json.loads(urlopen.call_args.args[0].data)
        self.assertEqual("image/webp", sent["contents"][0]["parts"][1]["inline_data"]["mime_type"])

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-secret"})
    @patch("app.garden_analysis.request.urlopen")
    def test_provider_503(self, urlopen):
        urlopen.side_effect = HTTPError("https://example.invalid", 503, "Unavailable", {}, None)
        with self.assertRaisesRegex(RuntimeError, "503"):
            analyze_image(self.image, "image/webp")

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-secret"})
    @patch("app.garden_analysis.request.urlopen")
    def test_rejects_invalid_feature_types(self, urlopen):
        self.analysis["description"]["features"]["lawn"] = "yes"
        provider = {"candidates": [{"content": {"parts": [{"text": json.dumps(self.analysis)}]}}]}
        urlopen.return_value = FakeResponse(provider)
        with self.assertRaisesRegex(RuntimeError, "features contract"):
            analyze_image(self.image, "image/webp")


if __name__ == "__main__":
    unittest.main()
