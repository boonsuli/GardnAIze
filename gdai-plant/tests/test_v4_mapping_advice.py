import pytest
from matching.questionnaire_mapping import map_questionnaire
from matching.advice_engine import render_advice, ADVICE
from matching.compensation_engine import evaluate_v4
from matching.label_candidate_pairs import load_config
from test_compensation_engine import fixture

def test_mapping():
    assert map_questionnaire({"exposure":"SHADE","waterAvailability":"MODERATE",
        "soilType":"LOAMY","evergreenPreferred":"YES"}) == {
        "sun_exposure":"FULL_SHADE","water_availability":"MEDIUM",
        "soil_texture":"SILT","evergreen_preferred":True}

def test_unknown_and_no_implicit_consent():
    assert map_questionnaire({"exposure":"UNKNOWN","maintenancePreference":"HIGH",
        "evergreenPreferred":"NO_PREFERENCE","matureSpread":"UNDER_1M"}) == {
        "maintenance_preference":"HIGH","mature_spread_preference":"UNDER_1M"}

def test_bilingual_catalogue():
    for key in ADVICE:
        fr = render_advice([key,key],"FR")
        en = render_advice([key],"EN")
        assert len(fr) == len(en) == 1
        assert fr[0]["text"] != en[0]["text"]
    with pytest.raises(ValueError):
        render_advice([], "XX")

@pytest.mark.parametrize("field,value,action,advice", [
    ("soil_drainage","POOR","drainage_improvement_accepted","DRAINAGE_IMPROVEMENT"),
    ("soil_moisture_seasonality","DRY_SUMMER","mulching_accepted","MULCHING"),
    ("soil_moisture_seasonality","SEASONAL_WET","raised_bed_accepted","RAISED_BED"),
])
def test_extended_compensation(field,value,action,advice):
    g,p,c = fixture()
    g[field] = value
    flags = {action:True}
    assert not evaluate_v4(g,p,c)["recommendation_eligible"]
    result = evaluate_v4(g,p,c,accepted=flags,feasible=flags)
    assert result["recommendation_eligible"]
    assert advice in result["usage_advice"]

def test_pruning_requires_feasibility():
    g,p,c = fixture()
    p["height_cm"] = [250,400]
    flags = {"regular_pruning_accepted":True}
    assert evaluate_v4(g,p,c,accepted=flags)["relevance_grade"] == 1
    assert evaluate_v4(g,p,c,accepted=flags,feasible=flags)["relevance_grade"] == 2
