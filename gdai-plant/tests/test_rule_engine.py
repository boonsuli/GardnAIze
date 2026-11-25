import unittest
from matching.label_candidate_pairs import grade, load_config

class RuleEngineTest(unittest.TestCase):
    def setUp(self):
        self.g=dict(sun_exposure="FULL_SUN",soil_drainage="GOOD",soil_texture="LOAM",
                    soil_moisture_seasonality="WELL_DRAINED",planting_context="IN_GROUND_BORDER",
                    minimum_winter_temperature_c=-8,water_availability="MEDIUM",
                    maximum_height_cm=80,maximum_spread_cm=60,evergreen_preferred=False)
        self.p=dict(category="SHRUB",sun_exposure=["FULL_SUN"],soil_drainage=["GOOD"],
                    soil_type=["LOAM"],soil_moisture_tolerance=["WELL_DRAINED"],
                    planting_context=["IN_GROUND_BORDER","HEDGE"],hardiness_min_c=-15,
                    water_need="MEDIUM",height_cm=[30,60],spread_cm=[30,60],evergreen=True)
    def grade(self):
        return grade(self.g,self.p,"v3")
    def test_compact(self):
        self.assertEqual(self.grade()[0],2)
    def test_tree(self):
        self.p["category"]="TREE"
        self.assertEqual(self.grade()[0],1)
    def test_large_shrub(self):
        self.p["height_cm"]=[250,400]
        self.assertEqual(self.grade()[0],1)
    def test_managed_hedge(self):
        self.g["planting_context"]="HEDGE"
        self.p["height_cm"]=[250,400]
        self.assertEqual(self.grade()[0],2)
    def test_environment_priority(self):
        self.p["category"]="TREE"
        self.g["sun_exposure"]="FULL_SHADE"
        self.assertEqual(self.grade()[0],0)
    def test_unknown(self):
        self.p["hardiness_min_c"]=None
        self.assertIsNone(self.grade()[0])
    def test_preference(self):
        self.g["evergreen_preferred"]=True
        self.assertEqual(self.grade()[0],3)
    def test_disable_landscape_rule(self):
        self.p["category"]="TREE"
        config=load_config()
        config["enabled_rules"].remove("PAYS-001")
        self.assertEqual(grade(self.g,self.p,"v3",config)[0],2)
    def test_unknown_rule(self):
        config=load_config()
        config["enabled_rules"].append("INVALID")
        with self.assertRaises(ValueError):
            grade(self.g,self.p,"v3",config)
