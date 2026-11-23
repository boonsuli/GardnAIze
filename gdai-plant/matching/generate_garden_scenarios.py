"""Generate garden proposals offline by default; paid API requires explicit CLI opt-in."""
import argparse
import json
import os
from pathlib import Path
from matching.realistic_scenarios import validate_batch

PROMPT = """You are assisting a French temperate-climate garden dataset project.
Return a JSON object with a 'scenarios' array of {count} realistic residential
garden scenarios. Prefer 60% common, 30% constrained, 10% rare-but-plausible.
Scope: temperate mainland France, non-mountain lowland residential gardens.
Exclude mountain/high-altitude and Mediterranean climates for this MVP.
Represent realistic variation without assuming climate from a photo.
Describe ONE planting zone, not a whole garden.
Never fabricate observations, measurements or sources. All generated records
must have origin='SYNTHETIC_AI'. Do not generate contradictions or duplicates.
When uncertain, return fewer records. Each scenario must include:
id (unique string), sun_exposure (FULL_SUN/PARTIAL_SHADE/FULL_SHADE),
soil_drainage (POOR/MODERATE/GOOD), water_availability (LOW/MEDIUM/HIGH),
minimum_winter_temperature_c (number), maximum_height_cm (number),
maximum_spread_cm (number), evergreen_preferred (boolean),
origin, plausibility_reason (nonempty string), region (French area string),
climate_zone (TEMPERATE_OCEANIC/TEMPERATE_SEMI_CONTINENTAL/TEMPERATE_TRANSITIONAL),
terrain_type (LOWLAND), soil_texture (CLAY/LOAM/SAND/SILT/STONY/MIXED),
soil_moisture_seasonality (DRY_SUMMER/SEASONAL_WET/CONSISTENTLY_MOIST/WELL_DRAINED),
planting_context (IN_GROUND_BORDER/HEDGE/COURTYARD/RAISED_BED/PLANTER/RAIN_GARDEN).
Avoid ambiguous mountain valleys and unsupported claims of measured soil or climate.
Do not create scenarios tailored to a particular plant. No plant names.
Represent one planting zone per scenario. Do not claim expert validation.
Return JSON only."""

def check_api_authorization(args, parser):
    """Never infer consent from API credentials, environment or model selection."""
    if args.input_json:
        if args.allow_paid_api or args.confirm_api_spend:
            parser.error("Offline import must not include API-spend flags")
        return
    if not args.allow_paid_api or args.confirm_api_spend != "I_AUTHORIZE_GEMINI_API_COST":
        parser.error("No API calls by default. For a one-off paid call, explicitly pass "
                     "--allow-paid-api --confirm-api-spend I_AUTHORIZE_GEMINI_API_COST")
    if not args.model or not os.getenv("GEMINI_API_KEY"):
        parser.error("Both --model (or GDAI_PLANT_GEMINI_MODEL) and GEMINI_API_KEY required")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--model", default=os.getenv("GDAI_PLANT_GEMINI_MODEL"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--input-json", help="Offline validation of existing JSON; no API")
    parser.add_argument("--allow-paid-api", action="store_true",
                        help="Explicit one-command authorization for a Gemini API request")
    parser.add_argument("--confirm-api-spend", default=None,
                        help="Must equal I_AUTHORIZE_GEMINI_API_COST")
    args = parser.parse_args()
    if not 1 <= args.count <= 50:
        parser.error("--count must be 1..50 (batch limit)")
    check_api_authorization(args, parser)
    usage = None
    if args.input_json:
        data = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    else:
        try:
            from google import genai
        except ImportError:
            parser.error("Install optional dependency: pip install google-genai")
        # Exactly one generation request. No automatic retry, escalation, or paid review.
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        response = client.models.generate_content(
            model=args.model,
            contents=PROMPT.format(count=args.count),
            config={"response_mime_type": "application/json"},
        )
        usage_data = getattr(response, "usage_metadata", None)
        if usage_data:
            usage = {
                "prompt_tokens": getattr(usage_data, "prompt_token_count", None),
                "output_tokens": getattr(usage_data, "candidates_token_count", None),
                "total_tokens": getattr(usage_data, "total_token_count", None),
            }
        data = json.loads(response.text)
    # Offline replay also accepts a prior result file with a "reviews" array.
    scenarios = data.get("scenarios") if isinstance(data, dict) else None
    if scenarios is None and isinstance(data, dict) and isinstance(data.get("reviews"), list):
        scenarios = [item.get("scenario") for item in data["reviews"] if isinstance(item, dict)]
    if not isinstance(scenarios, list):
        parser.error("Expected JSON object with scenarios array")
    if len(scenarios) > args.count:
        parser.error("Gemini returned more scenarios than requested")
    reviews = validate_batch(scenarios)
    result = {"schema_version": "1.2",
              "generator": "GEMINI" if not args.input_json else "IMPORTED",
              "model": args.model if not args.input_json else None,
              "api_usage": usage, "requested_count": args.count,
              "summary": {status: sum(r.status == status for r in reviews)
                          for status in ("ACCEPTED", "REVIEW_REQUIRED", "REJECTED")},
              "reviews": [r.to_dict() for r in reviews]}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "api_usage": usage}))

if __name__ == "__main__":
    main()
