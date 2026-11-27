import copy
from matching.dataset_quality import audit


def test_scope_is_configurable_and_does_not_mutate():
    document = {"scenarios": [{"id": "G1", "climate_zone": "OCEANIC",
                              "minimum_winter_temperature_c": -8}]}
    before = copy.deepcopy(document)
    profile = {"schema_version": 1, "profile_id": "test",
               "target_gardens": 1,
               "allowed_values": {"climate_zone": ["TRANSITIONAL"]},
               "numeric_ranges": {"minimum_winter_temperature_c": {"min": -7, "max": 0}}}
    assert audit(document, profile)["flagged"] == 1
    assert len(audit(document, profile)["issues"]) == 2
    profile["allowed_values"]["climate_zone"] = ["OCEANIC"]
    profile["numeric_ranges"]["minimum_winter_temperature_c"]["min"] = -10
    assert audit(document, profile)["flagged"] == 0
    assert document == before


def test_duplicate_and_invalid_number():
    document = {"scenarios": [{"id": "G1", "temperature": True},
                              {"id": "G1", "temperature": float("nan")}]}
    profile = {"schema_version": 1, "profile_id": "test", "target_gardens": 2,
               "numeric_ranges": {"temperature": {"min": -7, "max": 0}}}
    result = audit(document, profile)
    assert result["flagged"] == 2
    assert {i["code"] for i in result["issues"]} == {"DUPLICATE_ID", "INVALID_NUMBER"}
