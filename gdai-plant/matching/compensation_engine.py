"""Experimental V4 evaluation; V3 remains unchanged."""
from matching.rule_engine import evaluate

# Explicit commitments, not inferred from maintenance or budget preferences.
ACTIONS = {
    "HORT-002:frost_margin": ("frost_protection_accepted", "FROST_PROTECTION"),
    "HORT-004:water_need": ("supplemental_watering_accepted", "SUPPLEMENTAL_WATERING"),
    "HORT-005:soil_type": ("soil_amendment_accepted", "SOIL_AMENDMENT"),
    "HORT-003:soil_drainage": ("drainage_improvement_accepted", "DRAINAGE_IMPROVEMENT"),
    "PAYS-001:prefer_compact_vegetation": ("regular_pruning_accepted", "REGULAR_PRUNING"),
}

def evaluate_v4(garden, plant, config, *, accepted=None, feasible=None):
    """Resolve only conditional constraints with explicit acceptance and feasibility.

    Feasibility must be supplied by a separate assessment, not guessed here.
    Only specifically listed improvable drainage exclusions can be lifted.
    Other hard biological exclusions and missing evidence remain blocking.
    """
    initial, reasons = evaluate(garden, plant, config)
    accepted = accepted or {}
    feasible = feasible or {}
    resolved = []
    candidates = [("conditional", reason) for reason in reasons["conditional"]]
    candidates += [("incompatible", reason) for reason in reasons["incompatible"]
                   if reason == "HORT-003:soil_drainage"]
    for severity, reason in candidates:
        if reason == "PAYS-001:tree_in_restricted_space":
            reasons[severity].remove(reason)
            reasons["incompatible"].append(reason)
            continue
        action = ACTIONS.get(reason)
        if reason == "HORT-006:soil_moisture_tolerance":
            moisture = garden.get("soil_moisture_seasonality")
            tolerance = plant.get("soil_moisture_tolerance") or []
            if moisture == "DRY_SUMMER" and "WELL_DRAINED" in tolerance:
                action = ("mulching_accepted", "MULCHING")
            elif moisture == "SEASONAL_WET" and "WELL_DRAINED" in tolerance:
                action = ("raised_bed_accepted", "RAISED_BED")
        if reason == "PAYS-001:prefer_compact_vegetation" and plant.get("category") != "SHRUB":
            continue
        if action is None:
            continue
        commitment, advice = action
        if accepted.get(commitment) is True and feasible.get(commitment) is True:
            reasons[severity].remove(reason)
            resolved.append({"rule_id": reason.split(":")[0],
                             "condition": reason, "solution_id": commitment,
                             "advice_id": advice})
    # Preferences are independent of horticultural eligibility.
    preferences = {}
    color = garden.get("preferred_color")
    colors = plant.get("flower_color")
    if color and colors:
        preferences["flower_color_match"] = color.upper() in {v.upper() for v in colors}
    maintenance = garden.get("maintenance_preference")
    need = plant.get("maintenance_level")
    levels = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    if maintenance in levels and need in levels:
        preferences["maintenance_match"] = maintenance == need
        preferences["maintenance_gap"] = levels[need] - levels[maintenance]
    if garden.get("evergreen_preferred") is True:
        if "PREF-001:evergreen_preference" in reasons["conditional"]:
            reasons["conditional"].remove("PREF-001:evergreen_preference")
        if "PREF-001:evergreen" in reasons["unknown"]:
            reasons["unknown"].remove("PREF-001:evergreen")
        preferences["evergreen_match"] = plant.get("evergreen")
    final = (0 if reasons["incompatible"] else None if reasons["unknown"] else
             1 if reasons["conditional"] else 3 if reasons["matched"] else 2)
    return {"initial_relevance_grade": initial, "relevance_grade": final,
            "resolved_conditions": resolved,
            "unresolved_conditions": reasons["incompatible"] + reasons["unknown"] + reasons["conditional"],
            "usage_advice": sorted({item["advice_id"] for item in resolved}),
            "recommendation_eligible": final in (2, 3), "preference_assessment": preferences, "reasons": reasons}
