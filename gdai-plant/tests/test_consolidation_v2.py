import unittest
from enrichment.consolidate_plant_profiles import arbitrate

class ArbitrationTest(unittest.TestCase):
    def test_water(self):
        self.assertEqual(arbitrate("water_need","LOW","MEDIUM","CONTRADICTED")[0],"MEDIUM")
    def test_major(self):
        self.assertIsNone(arbitrate("water_need","LOW","HIGH","CONTRADICTED")[0])
    def test_dimensions(self):
        self.assertEqual(arbitrate("spread_cm",[150,300],[200,400],"CONTRADICTED")[0],[150,400])
    def test_intersection(self):
        self.assertEqual(arbitrate("soil_moisture_tolerance",["WELL_DRAINED","DRY_SUMMER"],["WELL_DRAINED"],"CONTRADICTED")[0],["WELL_DRAINED"])
    def test_uncertain(self):
        self.assertIsNone(arbitrate("hardiness_min_c",-12,None,"UNCERTAIN")[0])
    def test_catalogue(self):
        self.assertEqual(arbitrate("french_nursery_availability","IN_STOCK","LISTED","CONTRADICTED")[0],"LISTED")
    def test_heat(self):
        self.assertEqual(arbitrate("heat_tolerance","HIGH","MEDIUM","CONTRADICTED")[0],"MEDIUM")
