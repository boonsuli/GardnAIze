"""Suggest minimal preference changes that actually unlock a candidate."""
from itertools import combinations
from matching.compensation_engine import evaluate_v4

def suggest_alternatives(garden, plant, config, *, accepted=None, feasible=None):
    kwargs = {"accepted": accepted, "feasible": feasible}
    baseline = evaluate_v4(garden, plant, config, **kwargs)
    if baseline["recommendation_eligible"]:
        return []
    options = []
    if garden.get("evergreen_preferred") is True and plant.get("evergreen") is False:
        options.append(("evergreen_preferred", None, "evergreenPreferred", "YES", "NO_PREFERENCE"))
    if "PREF-002:flower_color" in baseline["unresolved_conditions"]:
        options.append(("preferred_color", None, "preferredColors", garden["preferred_color"], "NO_PREFERENCE"))
    if "PREF-003:maintenance_level" in baseline["unresolved_conditions"]:
        front = {"LOW":"LOW", "MEDIUM":"MODERATE", "HIGH":"HIGH"}
        options.append(("maintenance_preference", plant["maintenance_level"], "maintenancePreference",
                        front[garden["maintenance_preference"]], front[plant["maintenance_level"]]))
    for size in range(1, len(options)+1):
        for changes in combinations(options, size):
            candidate = dict(garden)
            candidate.update({key:value for key,value,*_ in changes})
            result = evaluate_v4(candidate, plant, config, **kwargs)
            if result["recommendation_eligible"]:
                return [{"question_key": question, "current_answer": old,
                         "suggested_answer": new,
                         "initial_relevance_grade": baseline["relevance_grade"],
                         "alternative_relevance_grade": result["relevance_grade"],
                         "usage_advice": result["usage_advice"]}
                        for _,_,question,old,new in changes]
    return []
