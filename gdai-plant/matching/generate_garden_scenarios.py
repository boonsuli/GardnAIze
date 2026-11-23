"""Generate *proposals* with Gemini, then validate them offline.

Requires GEMINI_API_KEY and the optional google-genai package.
Never stores scenarios in PostgreSQL or labels them as expert-validated.
"""
import argparse
import json
import os
from pathlib import Path
from matching.realistic_scenarios import validate_batch

PROMPT = """You are assisting a French temperate-climate garden dataset project.
Return a JSON object with a 'scenarios' array of {count} realistic residential
garden scenarios. Prefer 60% common, 30% constrained, 10% rare-but-plausible.
Never fabricate observations, measurements or sources. All generated records
must have origin='SYNTHETIC_AI'. Do not generate contradictions or duplicates.
When uncertain, return fewer records. Each scenario must include:
id (unique string), sun_exposure (FULL_SUN/PARTIAL_SHADE/FULL_SHADE),
soil_drainage (POOR/MODERATE/GOOD), water_availability (LOW/MEDIUM/HIGH),
minimum_winter_temperature_c (number), maximum_height_cm (number),
maximum_spread_cm (number), evergreen_preferred (boolean),
origin, plausibility_reason (nonempty string).
Do not create scenarios tailored to a particular plant. No plant names.
Represent one planting zone per scenario. Do not claim expert validation.
Return JSON only."""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--model", default=os.getenv("GDAI_PLANT_GEMINI_MODEL"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--input-json", help="Validate existing Gemini JSON without API call")
    args = parser.parse_args()
    if not 1 <= args.count <= 50:
        parser.error("--count must be 1..50 (batch limit)")
    if args.input_json:
        data = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    else:
        if not args.model or not os.getenv("GEMINI_API_KEY"):
            parser.error("GDAI_PLANT_GEMINI_MODEL/--model and GEMINI_API_KEY required")
        try:
            from google import genai
        except ImportError:
            parser.error("Install optional dependency: pip install google-genai")
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        response = client.models.generate_content(
            model=args.model,
            contents=PROMPT.format(count=args.count),
            config={"response_mime_type": "application/json"},
        )
        data = json.loads(response.text)
    scenarios = data.get("scenarios") if isinstance(data, dict) else None
    if not isinstance(scenarios, list):
        parser.error("Expected JSON object with scenarios array")
    if len(scenarios) > args.count:
        parser.error("Gemini returned more scenarios than requested")
    reviews = validate_batch(scenarios)
    result = {"schema_version": "1.0", "generator": "GEMINI" if not args.input_json else "IMPORTED",
              "requested_count": args.count,
              "summary": {status: sum(r.status == status for r in reviews)
                          for status in ("ACCEPTED", "REVIEW_REQUIRED", "REJECTED")},
              "reviews": [r.to_dict() for r in reviews]}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result["summary"]))

if __name__ == "__main__":
    main()
