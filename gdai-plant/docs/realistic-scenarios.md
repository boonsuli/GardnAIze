# Realistic garden scenario proposals (GDAI-PLANT)

**Offline by default: no API calls and no credit consumption without the user's explicit command.**

- Scenario checks are local Python code; they do not require Gemini or paid models.
- An API key or configured model alone **never** authorizes a request.
- A paid call requires **both** `--allow-paid-api` and `--confirm-api-spend I_AUTHORIZE_GEMINI_API_COST` on that command.
- One generation request maximum per invocation: no automatic retries, second model, premium escalation, or paid verification.
- No scheduled/background calls, no database writes, no Random Forest training.
- Token usage (when returned by the provider) is logged in the output; token counts are **not** a verified euro cost or spending cap.
- No claim that a more expensive model is faster or more accurate without an offline benchmark.
- `ACCEPTED` means automatic checks passed, **not** independent horticultural validation.

Run from `gdai-plant/`:

```bash
python -m unittest discover -s tests -p 'test_realistic_scenarios.py'
# Safe offline replay; does not require a Gemini key or SDK:
python -m matching.generate_garden_scenarios --count 50 --input-json /tmp/gemini.json --out /tmp/garden-reviews.json
```

Only when the user decides to spend credits:

```bash
pip install google-genai
export GEMINI_API_KEY=...  # do not commit
export GDAI_PLANT_GEMINI_MODEL=...  # choose an available model
python -m matching.generate_garden_scenarios --count 10 \
  --out /tmp/garden-reviews.json \
  --allow-paid-api --confirm-api-spend I_AUTHORIZE_GEMINI_API_COST
```

The live example requests **10** scenarios for a small pilot. The API provider may charge even when generation fails or validation rejects results. For strict monetary protection, configure an appropriate billing limit or monitoring at the provider; this script does not guarantee a euro spending cap.

Next steps: benchmark quality and latency using offline fixtures; add regional plausibility checks, near-duplicate detection and independent review before generating 50 scenarios x 40 plants = 2,000 *potential* pairs.
