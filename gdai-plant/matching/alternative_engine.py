"""Suggest only preference changes that actually unlock a candidate."""
from matching.compensation_engine import evaluate_v4

def suggest_alternatives(garden, plant, config, *, accepted=None, feasible=None):
    kwargs = {"accepted": accepted, "feasible": feasible}
    baseline = evaluate_v4(garden, plant, config, **kwargs)
    if baseline["recommendation_eligible"]:
        return []
    # Only evergreen preference is currently scored by the rule registry.
    if garden.get("evergreen_preferred") is not True or plant.get("evergreen") is not False:
        return []
    candidate = dict(garden, evergreen_preferred=None)
    result = evaluate_v4(candidate, plant, config, **kwargs)
    if not result["recommendation_eligible"]:
        return []
    return [{"question_key": "evergreenPreferred", "current_answer": "YES",
             "suggested_answer": "NO_PREFERENCE",
             "initial_relevance_grade": baseline["relevance_grade"],
             "alternative_relevance_grade": result["relevance_grade"],
             "usage_advice": result["usage_advice"]}]
