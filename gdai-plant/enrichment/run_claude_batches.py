"""Review existing Gemini profiles. No network by default; no automatic retries."""
import argparse
import json
import os
import re
from urllib.request import Request, urlopen
from enrichment.prepare_profile_pilot import ROOT
from enrichment.prepare_claude_review import prepare, digest
from enrichment.qualify_batches import qualify

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", required=True)
    p.add_argument("--max-requests", type=int, default=1)
    p.add_argument("--max-output-tokens", type=int, default=32768)
    p.add_argument("--allow-paid-api", action="store_true")
    p.add_argument("--confirm-api-spend")
    a = p.parse_args()
    if not 1 <= a.max_requests <= 20 or not 1 <= a.max_output_tokens <= 65536:
        p.error("Invalid request or token limit")
    key = os.getenv("ANTHROPIC_API_KEY")
    if a.allow_paid_api and (not key or a.confirm_api_spend != "I_AUTHORIZE_CLAUDE_API_COST"):
        p.error("Export ANTHROPIC_API_KEY and explicitly authorize Claude API cost")
    catalogue = json.loads((ROOT/"data/plants-mvp-100.json").read_text())
    work = ROOT/"data/enrichment/mvp-100"
    calls = 0
    batches = []
    for offset in range(0,len(catalogue),5):
        folder = work/f"batch-{offset//5+1:02d}"
        source, dest = folder/"profiles.json", folder/"review.json"
        if not source.exists():
            print(folder.name,"awaiting Gemini")
            continue
        names = [x["scientific_name"] for x in catalogue[offset:offset+5]]
        payload = json.loads(source.read_text())
        prompt = prepare(payload,names)
        if dest.exists():
            review = json.loads(dest.read_text())
            qualify(catalogue,[(names,payload,review)])
            batches.append((names,payload,review))
            print(folder.name,"already reviewed")
            continue
        print(folder.name,"review pending")
        if not a.allow_paid_api or calls >= a.max_requests:
            continue
        run = folder/"claude-run-v1"
        run.mkdir(exist_ok=False)
        (run/"request.json").write_text(json.dumps({"model":a.model,"input_sha256":digest(payload),"max_tokens":a.max_output_tokens},indent=2))
        (run/"prompt.txt").write_text(prompt,encoding="utf-8")
        req = Request("https://api.anthropic.com/v1/messages",
            data=json.dumps({"model":a.model,"max_tokens":a.max_output_tokens,"messages":[{"role":"user","content":prompt}]}).encode(),
            headers={"x-api-key":key,"anthropic-version":"2023-06-01","Content-Type":"application/json"})
        calls += 1
        with urlopen(req,timeout=600) as response:
            raw = response.read()
        (run/"response-raw.json").write_bytes(raw)
        result = json.loads(raw)
        (run/"usage.json").write_text(json.dumps(result.get("usage",{}),indent=2))
        if result.get("stop_reason") != "end_turn":
            raise ValueError(f"Incomplete Claude response: {result.get('stop_reason')}")
        text = "".join(x["text"] for x in result.get("content",[]) if x.get("type")=="text").strip()
        review = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$","",text))
        qualify(catalogue,[(names,payload,review)])
        with dest.open("x",encoding="utf-8") as f:
            json.dump(review,f,ensure_ascii=False,indent=2)
        batches.append((names,payload,review))
    _,_,report = qualify(catalogue,batches)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    print("Live Claude requests started:",calls)

if __name__ == "__main__":
    main()
