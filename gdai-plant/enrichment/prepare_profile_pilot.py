"""Prepare offline Gemini generation prompt."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRAITS = ("sun_exposure", "soil_drainage", "water_need", "hardiness_min_c",
          "height_cm", "spread_cm", "evergreen", "soil_type",
          "soil_moisture_tolerance", "planting_context", "root_development",
          "heat_tolerance", "drought_tolerance", "maintenance_level",
          "flower_color", "flowering_months", "french_nursery_availability")

def prepare(plants, protocol, offset=0, count=5):
    if offset < 0 or not 1 <= count <= 5 or offset + count > len(plants):
        raise ValueError("Invalid batch; maximum five plants")
    names = [p["scientific_name"] for p in plants[offset:offset+count]]
    template = {"profiles": [{"scientific_name": "<requested name>",
        "traits": {k: {"value": None, "source_urls": [], "notes": "Explain evidence or uncertainty", "evidence_status": "UNKNOWN"} for k in TRAITS}}]}
    return protocol + "\nRequested names: " + json.dumps(names, ensure_ascii=False) + "\nReturn this structure for each requested name:\n" + json.dumps(template, indent=2) + "\n"

def with_sources(protocol, sources):
    return protocol + "\nPreferred documentary source registry (unverified leads):\n" + json.dumps(sources, ensure_ascii=False, indent=2) + "\n"

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--count", type=int, default=5)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    plants = json.loads((ROOT / "data/plants-mvp-40.json").read_text(encoding="utf-8"))
    protocol = (ROOT / "prompts/horticultural-common-v1.md").read_text(encoding="utf-8")
    sources = json.loads((ROOT / "config/gardnaize-horticultural-sources-v1.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schemas/plant-enrichment-v1.schema.json").read_text(encoding="utf-8"))
    protocol += "\nThe following JSON Schema is authoritative:\n" + json.dumps(schema, ensure_ascii=False) + "\n"
    prompt = prepare(plants, with_sources(protocol, sources), a.offset, a.count)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("x", encoding="utf-8") as f:
        f.write(prompt)
    print(f"Prepared {a.count} plants; zero API calls")

if __name__ == "__main__":
    main()
