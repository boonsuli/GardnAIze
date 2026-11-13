"""Unit tests: no network, PostgreSQL or third-party datasets required."""
import tempfile
import unittest
from pathlib import Path

from pipeline import canonical_key, eligible, merge_records, read_authorized_csv

class PlantIngestionTests(unittest.TestCase):
    def test_canonical_name_and_cultivar(self):
        self.assertEqual(canonical_key({"scientific_name":"  Lavandula   angustifolia ",
                                        "cultivar":"Hidcote"}),
                         ("lavandula angustifolia","hidcote"))

    def test_reject_unapproved_source(self):
        with self.assertRaises(PermissionError):
            list(read_authorized_csv("missing.csv",{"name":"merchant",
                 "source_url":"https://example.org","license":"CC0-1.0",
                 "automated_access_allowed":False,"commercial_reuse_allowed":True}))

    def test_merge_and_conflict(self):
        a={"scientific_name":"Lavandula angustifolia","cultivar":None,
           "outdoor":"true","europe_compatible":"true","source":"open",
           "exposure":"FULL_SUN","soil":None}
        b=dict(a,source="merchant",soil="SANDY",exposure="PARTIAL_SHADE")
        plants, conflicts=merge_records([a,b])
        self.assertEqual(len(plants),1)
        self.assertEqual(plants[0]["soil"],"SANDY")
        self.assertEqual(len(conflicts),1)
        self.assertEqual(plants[0]["quality_status"],"INCOMPLETE")

    def test_europe_filter(self):
        self.assertFalse(eligible({"outdoor":"true","europe_compatible":"false"}))

if __name__=="__main__":
    unittest.main()
