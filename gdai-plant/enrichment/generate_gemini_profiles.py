"""One explicitly authorized Gemini REST request with Google Search grounding."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from urllib.request import Request, urlopen
from enrichment.prepare_profile_pilot import ROOT
from enrichment.validate_plant_profiles import validate

def extract(response):
    candidates = response.get("candidates", [])
    if len(candidates) != 1 or candidates[0].get("finishReason") != "STOP":
        raise ValueError(f"Incomplete Gemini response: candidates={len(candidates)}, finishReasons={[c.get('finishReason') for c in candidates]}")
    c = candidates[0]
    raw = "".join(p.get("text", "") for p in c["content"]["parts"] if not p.get("thought"))
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
    return json.loads(raw)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prompt", type=Path)
    p.add_argument("--input-json", type=Path, help="Replay saved raw response without API calls")
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--model")
    p.add_argument("--max-output-tokens", type=int, default=16384)
    p.add_argument("--catalogue", type=Path, default=ROOT / "data/plants-mvp-40.json")
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--count", type=int, default=5)
    p.add_argument("--allow-paid-api", action="store_true")
    p.add_argument("--confirm-api-spend")
    a = p.parse_args()
    if not 1 <= a.max_output_tokens <= 65536:
        p.error("Invalid output token limit")
    if not a.input_json and (not a.model or not re.fullmatch(r"[A-Za-z0-9._-]+", a.model)):
        p.error("Invalid model ID")
    plants = json.loads(a.catalogue.read_text(encoding="utf-8"))
    if a.offset < 0 or not 1 <= a.count <= 5 or a.offset+a.count > len(plants):
        p.error("Invalid batch")
    names = [x["scientific_name"] for x in plants[a.offset:a.offset+a.count]]
    if a.input_json:
        raw = a.input_json.read_bytes()
        a.out_dir.mkdir(parents=True, exist_ok=False)
    else:
        if not a.prompt:
            p.error("--prompt is required for live generation")
        prompt = a.prompt.read_text(encoding="utf-8")
        if "Requested names: " + json.dumps(names, ensure_ascii=False) not in prompt:
            p.error("Prompt does not match requested batch")
        if not a.allow_paid_api or a.confirm_api_spend != "I_AUTHORIZE_GEMINI_API_COST":
            p.error("Paid API requires explicit authorization")
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            p.error("Set GEMINI_API_KEY or GOOGLE_API_KEY")
        a.out_dir.mkdir(parents=True, exist_ok=False)
        body = {"contents": [{"parts": [{"text": prompt}]}],
                "tools": [{"google_search": {}}],
                "generationConfig": {"maxOutputTokens": a.max_output_tokens}}
        metadata = {"model": a.model, "names": names, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "status": "REQUEST_STARTED", "max_output_tokens": a.max_output_tokens}
        (a.out_dir / "request.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        (a.out_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
        req = Request("https://generativelanguage.googleapis.com/v1beta/models/" + a.model + ":generateContent",
                      data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key})
        with urlopen(req, timeout=300) as response:
            raw = response.read()
    (a.out_dir / "response-raw.json").write_bytes(raw)
    response = json.loads(raw)
    print(json.dumps(response.get("usageMetadata", {})))
    (a.out_dir / "usage.json").write_text(json.dumps(response.get("usageMetadata", {}), indent=2), encoding="utf-8")
    payload = extract(response)
    (a.out_dir / "profiles-unvalidated.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report = validate(payload, names)
    report["grounding_present"] = bool(response["candidates"][0].get("groundingMetadata", {}).get("groundingChunks"))
    report["documentary_status"] = "UNVERIFIED"
    report["api_calls"] = 0 if a.input_json else 1
    (a.out_dir / "validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))

if __name__ == "__main__":
    main()
