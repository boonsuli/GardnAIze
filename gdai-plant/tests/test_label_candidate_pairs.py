import unittest
from matching.label_candidate_pairs import grade, build

class MatchingTest(unittest.TestCase):
    def setUp(self):
        self.g = dict(id="G1",origin="SYNTHETIC_AI",sun_exposure="FULL_SUN",soil_drainage="GOOD",
                      soil_texture="LOAM",soil_moisture_seasonality="WELL_DRAINED",
                      planting_context="HEDGE",minimum_winter_temperature_c=-8,
                      water_availability="MEDIUM",maximum_height_cm=400,maximum_spread_cm=400,
                      evergreen_preferred=False)
        self.p = dict(sun_exposure=["FULL_SUN"],soil_drainage=["GOOD"],soil_type=["LOAM"],
                      soil_moisture_tolerance=["WELL_DRAINED"],planting_context=["HEDGE"],
                      hardiness_min_c=-15,water_need="MEDIUM",height_cm=[200,350],
                      spread_cm=[150,300],evergreen=True)
    def test_compatible(self):
        self.assertEqual(grade(self.g,self.p)[0],2)
    def test_preference(self):
        self.g["evergreen_preferred"]=True
        self.assertEqual(grade(self.g,self.p)[0],3)
    def test_frost(self):
        self.g["minimum_winter_temperature_c"]=-16
        self.assertEqual(grade(self.g,self.p)[0],0)
    def test_unknown(self):
        self.p["hardiness_min_c"]=None
        self.assertIsNone(grade(self.g,self.p)[0])
    def test_dimensions(self):
        self.g["maximum_height_cm"]=250
        self.assertEqual(grade(self.g,self.p)[0],1)
        self.g["maximum_height_cm"]=100
        self.assertEqual(grade(self.g,self.p)[0],0)
    def test_water(self):
        self.g["water_availability"]="LOW"
        self.assertEqual(grade(self.g,self.p)[0],1)
        self.p["water_need"]="HIGH"
        self.assertEqual(grade(self.g,self.p)[0],0)
    def test_quality_gate(self):
        profiles={"profiles":[{"scientific_name":"A","traits":{k:{"value":v} for k,v in self.p.items()}}]}
        for status in ("ACCEPTED","CONDITIONAL","EXCLUDED"):
            with self.subTest(status=status):
                row=build([self.g],profiles,{"policy":"PROVISIONAL_V2","plants":[{"scientific_name":"A","status":status}]})[0]
                self.assertEqual(row["experimental_training_eligible"],status=="ACCEPTED")
                if status=="EXCLUDED":
                    self.assertIsNone(row["relevance_grade"])
    def test_known_incompatibility_with_unknown(self):
        self.p["hardiness_min_c"]=None
        self.g["sun_exposure"]="FULL_SHADE"
        self.assertEqual(grade(self.g,self.p)[0],0)
