"""Offline sensitivity experiment, not observed user consent or site assessment."""
import argparse
import json
from pathlib import Path
from enrichment.prepare_claude_review import digest

def enrich(document):
    rows = []
    for i, source in enumerate(document["scenarios"]):
        g = dict(source)
        if "compensation_accepted" in g or "compensation_feasible" in g:
            raise ValueError("Already enriched")
        # Independent hypothetical user profiles, never selected by plant labels.
        maintenance = ("LOW", "MEDIUM", "HIGH")[i % 3]
        g["maintenance_preference"] = maintenance
        if i % 4:
            g["preferred_color"] = ("WHITE", "PINK", "PURPLE", "YELLOW")[(i // 4) % 4]
        accepted = {
            "supplemental_watering_accepted": maintenance != "LOW",
            "mulching_accepted": i % 5 != 0,
            "soil_amendment_accepted": maintenance != "LOW",
            "drainage_improvement_accepted": maintenance == "HIGH",
            "raised_bed_accepted": maintenance == "HIGH",
            "regular_pruning_accepted": maintenance == "HIGH",
            "frost_protection_accepted": maintenance != "LOW",
        }
        # Hypothetical site assumptions; plant-specific feasibility stays unknown.
        feasible = {
            "mulching_accepted": g.get("soil_moisture_seasonality") == "DRY_SUMMER"
                and g.get("soil_drainage") in ("GOOD", "MODERATE"),
            "supplemental_watering_accepted": g.get("water_availability") == "MEDIUM",
        }
        g.update(compensation_accepted=accepted, compensation_feasible=feasible,
                 compensation_provenance="SYNTHETIC_SENSITIVITY_V1")
        rows.append(g)
    return {**document, "scenarios": rows, "source_sha256": digest(document["scenarios"]),
            "compensation_status": "SYNTHETIC_NOT_OBSERVED_NOT_EXPERT_VALIDATED"}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    result = enrich(json.loads(a.input.read_text(encoding="utf-8")))
    with a.out.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"{len(result['scenarios'])} synthetic scenarios; zero API calls")

if __name__ == "__main__":
    main()
