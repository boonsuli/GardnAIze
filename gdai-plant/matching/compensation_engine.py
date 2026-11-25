"""Experimental V4 evaluation; V3 remains unchanged."""
from matching.rule_engine import evaluate

# Explicit commitments, not inferred from maintenance or budget preferences.
ACTIONS = {
    "HORT-002:frost_margin": ("frost_protection_accepted", "FROST_PROTECTION"),
    "HORT-004:water_need": ("supplemental_watering_accepted", "SUPPLEMENTAL_WATERING"),
    "HORT-005:soil_type": ("soil_amendment_accepted", "SOIL_AMENDMENT"),
}

def evaluate_v4(garden, plant, config, *, accepted=None, feasible=None):
    """Resolve only conditional constraints with explicit acceptance and feasibility.

    Feasibility must be supplied by a separate assessment, not guessed here.
    Hard biological exclusions and missing evidence remain blocking.
    """
    initial, reasons = evaluate(garden, plant, config)
    accepted = accepted or {}
    feasible = feasible or {}
    resolved = []
    for reason in list(reasons["conditional"]):
        if reason == "PAYS-001:tree_in_restricted_space":
            reasons["conditional"].remove(reason)
            reasons["incompatible"].append(reason)
            continue
        action = ACTIONS.get(reason)
        if action is None:
            continue
        commitment, advice = action
        if accepted.get(commitment) is True and feasible.get(commitment) is True:
            reasons["conditional"].remove(reason)
            resolved.append({"rule_id": reason.split(":")[0],
                             "condition": reason, "solution_id": commitment,
                             "advice_id": advice})
    final = (0 if reasons["incompatible"] else None if reasons["unknown"] else
             1 if reasons["conditional"] else 3 if reasons["matched"] else 2)
    return {"initial_relevance_grade": initial, "relevance_grade": final,
            "resolved_conditions": resolved,
            "unresolved_conditions": reasons["incompatible"] + reasons["unknown"] + reasons["conditional"],
            "usage_advice": sorted({item["advice_id"] for item in resolved}),
            "recommendation_eligible": final in (2, 3), "reasons": reasons}
