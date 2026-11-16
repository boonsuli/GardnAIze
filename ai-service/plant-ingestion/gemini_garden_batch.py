"""Analyse accepted ML garden images with Gemini Vision and persist reviewed=false.

No user application photos are accessed. Dry-run by default; --apply sends images
to Gemini and stores observations. External image transfer requires lawful rights.
"""
import argparse
import base64
import json
import mimetypes
import os
import hashlib
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

KEYS = ("lawn","terrace","pathway","trees","shrubs","fence","low_wall","stairs","slope")
PROMPT = """Analyze this garden photograph. Return ONLY a JSON object with keys
lawn, terrace, pathway, trees, shrubs, fence, low_wall, stairs, slope, each boolean true/false if
visually clear; use null when uncertain or not visible. Do not infer soil,
climate, sun hours, garden size, or plant species. Include a short 'notes'
string. Treat absence of evidence as null, not false."""

def analyze(path, key, model):
    mime = mimetypes.guess_type(str(path))[0]
    if mime not in ("image/jpeg","image/png","image/webp"):
        raise ValueError(f"Unsupported image format: {path}")
    if path.stat().st_size > 5 * 1024 * 1024:
        raise ValueError("Image exceeds 5 MiB")
    payload = {"contents":[{"parts":[{"text":PROMPT},{"inline_data":{
        "mime_type":mime,"data":base64.b64encode(path.read_bytes()).decode("ascii")
    }}]}],"generationConfig":{"responseMimeType":"application/json","temperature":0}}
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    request=Request(url,data=json.dumps(payload).encode(),headers={
        "Content-Type":"application/json","x-goog-api-key":key},method="POST")
    with urlopen(request,timeout=75) as response:
        result=json.load(response)
    parts=result["candidates"][0]["content"]["parts"]
    raw="".join(part.get("text","") for part in parts)
    features=json.loads(raw)
    if not isinstance(features,dict):
        raise ValueError("Gemini response must be an object")
    for name in KEYS:
        if name not in features or features[name] not in (True,False,None):
            raise ValueError(f"Invalid or missing feature {name}")
    return features, result.get("usageMetadata", {})

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--apply",action="store_true",help="Send images to Gemini and save results")
    parser.add_argument("--limit",type=int,default=31)
    parser.add_argument("--model",default=os.getenv("GEMINI_VISION_MODEL","gemini-2.5-flash"))
    parser.add_argument("--image-root",type=Path,default=Path("ai-service/plant-ingestion/inputs/images"))
    args=parser.parse_args()
    if not 1<=args.limit<=1000:
        raise SystemExit("--limit must be between 1 and 1000")
    dsn=os.getenv("GARDNAIZE_ML_DATABASE_URL")
    if not dsn:
        raise SystemExit("GARDNAIZE_ML_DATABASE_URL required")
    import psycopg
    # Accept both SQLAlchemy URLs and native psycopg URLs without logging secrets.
    if dsn.startswith("postgresql+psycopg://"):
        dsn = "postgresql://" + dsn[len("postgresql+psycopg://"):]
    elif dsn.startswith("postgresql+psycopg2://"):
        dsn = "postgresql://" + dsn[len("postgresql+psycopg2://"):]
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT g.image_id,g.image_uri FROM horticulture.garden_image_candidate g
              LEFT JOIN horticulture.ml_garden_features f ON f.image_id=g.image_id
              WHERE g.review_status='ACCEPTED' AND f.image_id IS NULL
              ORDER BY g.image_id LIMIT %s""",(args.limit,))
            rows=cur.fetchall()
        print(f"Unanalyzed accepted garden images: {len(rows)}; apply={args.apply}")
        if not args.apply:
            return
        key=os.getenv("GEMINI_API_KEY")
        if not key:
            raise SystemExit("GEMINI_API_KEY required for --apply")
        root=args.image_root.resolve()
        for image_id,uri in rows:
            try:
                image_path=Path(uri).resolve()
                if not image_path.is_relative_to(root) or not image_path.is_file():
                    raise ValueError("Image not found inside approved local image root")
                features, usage=analyze(image_path,key,args.model)
                with conn.cursor() as cur:
                    cur.execute("""INSERT INTO horticulture.ml_garden_features
                      (image_id,feature_values,feature_source,feature_model_version,reviewed)
                      VALUES (%s,%s::jsonb,'GEMINI_VISION',%s,false)
                      ON CONFLICT (image_id) DO NOTHING""",
                      (image_id,json.dumps(features,ensure_ascii=False),args.model))
                    cur.execute("""INSERT INTO horticulture.ml_gemini_usage
                      (image_id,model_name,prompt_tokens,output_tokens,total_tokens,
                       image_sha256,request_status)
                      VALUES (%s,%s,%s,%s,%s,%s,'SUCCEEDED')""",
                      (image_id,args.model,usage.get("promptTokenCount"),
                       usage.get("candidatesTokenCount"),usage.get("totalTokenCount"),
                       hashlib.sha256(image_path.read_bytes()).hexdigest()))
                conn.commit()
                print(f"Saved image_id={image_id} reviewed=false usage={usage}")
            except (ValueError,KeyError,HTTPError,URLError,TimeoutError,OSError) as exc:
                conn.rollback()
                print(f"FAILED image_id={image_id}: {type(exc).__name__}: {exc}")
if __name__=="__main__":
    main()
