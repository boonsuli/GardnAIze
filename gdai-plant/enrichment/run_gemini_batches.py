"""Dry-run by default. Request-count cap, not a monetary guarantee."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from enrichment.prepare_profile_pilot import ROOT
from enrichment.validate_plant_profiles import validate

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", required=True)
    p.add_argument("--max-output-tokens", type=int, default=32768)
    p.add_argument("--max-requests", type=int, default=1)
    p.add_argument("--allow-paid-api", action="store_true")
    p.add_argument("--confirm-api-spend")
    a = p.parse_args()
    if not 1 <= a.max_output_tokens <= 65536:
        p.error("Invalid output token limit")
    if not 1 <= a.max_requests <= 20:
        p.error("Request cap must be 1..20")
    if a.allow_paid_api and a.confirm_api_spend != "I_AUTHORIZE_GEMINI_API_COST":
        p.error("Explicit authorization required")
    catalogue = ROOT/"data/plants-mvp-100.json"
    plants = json.loads(catalogue.read_text())
    work = ROOT/"data/enrichment/mvp-100"
    calls = 0
    for offset in range(0,len(plants),5):
        folder = work/f"batch-{offset//5+1:02d}"
        count = min(5,len(plants)-offset)
        names = [p["scientific_name"] for p in plants[offset:offset+count]]
        dest = folder/"profiles.json"
        if dest.exists():
            validate(json.loads(dest.read_text()),names)
            print(folder.name,"already complete")
            continue
        attempts = sorted(folder.glob("gemini-run-v*"), key=lambda p: int(p.name.rsplit("v",1)[1]))
        run = attempts[-1] if attempts else folder/"gemini-run-v1"
        if run.exists():
            validated = run/"validation.json"
            if not validated.exists():
                raise RuntimeError(f"Unresolved prior attempt: {run}; inspect raw response before retry")
            payload = json.loads((run/"profiles-unvalidated.json").read_text())
            validate(payload,names)
            if a.allow_paid_api:
                with dest.open("x",encoding="utf-8") as f:
                    json.dump(payload,f,ensure_ascii=False,indent=2)
            print(folder.name,"recoverable")
            continue
        prompt = folder/"gemini-prompt.txt"
        if not prompt.is_file():
            raise FileNotFoundError(prompt)
        print(folder.name,"pending")
        if not a.allow_paid_api or calls >= a.max_requests:
            continue
        calls += 1
        subprocess.run([sys.executable,"-m","enrichment.generate_gemini_profiles",
            "--catalogue",str(catalogue),"--offset",str(offset),"--count",str(count),
            "--prompt",str(prompt),"--out-dir",str(run),"--model",a.model,
            "--max-output-tokens",str(a.max_output_tokens),
            "--allow-paid-api","--confirm-api-spend",a.confirm_api_spend],cwd=ROOT,check=True)
        payload = json.loads((run/"profiles-unvalidated.json").read_text())
        validate(payload,names)
        with dest.open("x",encoding="utf-8") as f:
            json.dump(payload,f,ensure_ascii=False,indent=2)
    print("Live requests started:",calls)

if __name__ == "__main__":
    main()
