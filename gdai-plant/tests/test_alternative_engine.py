from matching.alternative_engine import suggest_alternatives
from matching.label_candidate_pairs import grade
from test_compensation_engine import fixture

def test_alternative_unlocks_plant_without_mutation():
    g,p,c = fixture()
    g["evergreen_preferred"] = True
    p["evergreen"] = False
    original = dict(g)
    result = suggest_alternatives(g,p,c)
    assert len(result) == 1
    assert result[0]["suggested_answer"] == "NO_PREFERENCE"
    assert result[0]["alternative_relevance_grade"] == 2
    assert g == original

def test_alternative_does_not_hide_exposure_conflict():
    g,p,c = fixture()
    g.update(evergreen_preferred=True, sun_exposure="FULL_SHADE")
    p["evergreen"] = False
    assert suggest_alternatives(g,p,c) == []

def test_alternative_does_not_hide_unknown():
    g,p,c = fixture()
    g["evergreen_preferred"] = True
    p.update(evergreen=False, hardiness_min_c=None)
    assert suggest_alternatives(g,p,c) == []

def test_no_alternative_for_compatible_plant():
    g,p,c = fixture()
    assert suggest_alternatives(g,p,c) == []

def test_v4_dispatch_preserves_v3():
    g,p,c = fixture()
    p["category"] = "TREE"
    assert grade(g,p,"v3",c)[0] == 1
    assert grade(g,p,"v4",c)[0] == 0
