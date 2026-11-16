"""Offline tests for source mapping and Gemini response validation helpers."""
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from io import BytesIO

ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT))
from questionnaire_plant_mapping import QUESTION_MAPPING
from gbif_taxonomy import match

class DummyResponse:
    def __init__(self, payload):
        self.payload=payload
    def __enter__(self):
        return self
    def __exit__(self,*args):
        return False
    def read(self):
        return json.dumps(self.payload).encode()

class IngestionTests(unittest.TestCase):
    def test_questionnaire_coverage(self):
        self.assertTrue({"exposure","soil","water","maintenance","evergreen",
                         "flower_color","height_max","privacy","budget","climate"}.issubset(QUESTION_MAPPING))
    def test_gbif_name_matching_provenance(self):
        response={"scientificName":"Lavandula angustifolia Mill.",
                  "canonicalName":"Lavandula angustifolia","usageKey":123,
                  "matchType":"EXACT","confidence":100}
        with patch("gbif_taxonomy.urlopen",return_value=DummyResponse(response)):
            item=match("Lavandula angustifolia")
        self.assertEqual(item["gbif_usage_key"],123)
        self.assertIn("api.gbif.org",item["source_url"])
        self.assertEqual(item["input_name"],"Lavandula angustifolia")
if __name__=="__main__":
    unittest.main()
