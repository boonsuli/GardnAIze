"""Preference alternatives for horticulturally eligible candidates."""
from matching.compensation_engine import evaluate_v4

def suggest_alternatives(garden, plant, config, *, accepted=None, feasible=None):
    result = evaluate_v4(garden, plant, config, accepted=accepted, feasible=feasible)
    if not result["recommendation_eligible"]:
        return []
    changes = []
    preferences = result["preference_assessment"]
    if preferences.get("evergreen_match") is False:
        changes.append(("evergreenPreferred", "YES", "NO_PREFERENCE"))
    front = {"LOW":"LOW", "MEDIUM":"MODERATE", "HIGH":"HIGH"}
    if preferences.get("maintenance_gap", 0) != 0:
        changes.append(("maintenancePreference", front[garden["maintenance_preference"]],
                        front[plant["maintenance_level"]]))
    return [{"question_key": question, "current_answer": old,
             "suggested_answer": new, "alternative_type": "PREFERENCE_SELECTION",
             "initial_relevance_grade": result["relevance_grade"],
             "alternative_relevance_grade": result["relevance_grade"],
             "usage_advice": result["usage_advice"]}
            for question, old, new in changes]
