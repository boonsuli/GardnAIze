from matching.compensation_engine import evaluate_v4
from matching.label_candidate_pairs import load_config
from test_rule_engine import RuleEngineTest as _RuleEngineTest

def fixture():
    case = _RuleEngineTest()
    case.setUp()
    return case.g, case.p, load_config()

def test_explicit_compensation():
    g, p, c = fixture()
    g["water_availability"] = "LOW"
    action = {"supplemental_watering_accepted": True}
    result = evaluate_v4(g, p, c, accepted=action, feasible=action)
    assert result["initial_relevance_grade"] == 1
    assert result["relevance_grade"] == 2
    assert result["usage_advice"] == ["SUPPLEMENTAL_WATERING"]
    assert g["water_availability"] == "LOW"

def test_missing_feasibility_or_acceptance():
    g, p, c = fixture()
    g["water_availability"] = "LOW"
    action = {"supplemental_watering_accepted": True}
    for kwargs in ({}, {"accepted": action}, {"feasible": action}):
        assert evaluate_v4(g, p, c, **kwargs)["relevance_grade"] == 1

def test_tree_exclusion():
    g, p, c = fixture()
    p["category"] = "TREE"
    result = evaluate_v4(g, p, c)
    assert result["initial_relevance_grade"] == 1
    assert result["relevance_grade"] == 0
    assert not result["recommendation_eligible"]

def test_hard_exclusion_preserved():
    g, p, c = fixture()
    g["sun_exposure"] = "FULL_SHADE"
    g["water_availability"] = "LOW"
    action = {"supplemental_watering_accepted": True}
    assert evaluate_v4(g, p, c, accepted=action, feasible=action)["relevance_grade"] == 0

def test_unknown_preserved():
    g, p, c = fixture()
    p["hardiness_min_c"] = None
    assert evaluate_v4(g, p, c)["relevance_grade"] is None
