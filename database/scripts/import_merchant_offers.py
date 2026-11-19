"""Import licensed merchant offer JSON (prepared by authorized_sources.py). Dry-run by default."""
import argparse
import json
import os
from pathlib import Path

def import_offers(conn, offers):
    with conn.transaction():
        with conn.cursor() as cur:
            for o in offers:
                for key in ("source","scientific_name","external_offer_id","price_amount"):
                    if not o.get(key) and o.get(key)!=0: raise ValueError(f"Missing {key}")
                cur.execute("""
                  SELECT s.data_source_id,p.plant_id FROM horticulture.data_source s
                  CROSS JOIN horticulture.plant p
                  WHERE s.source_name=%s AND s.commercial_reuse_allowed IS TRUE
                    AND p.normalized_scientific_name=%s
                """,(o["source"]," ".join(o["scientific_name"].casefold().split())))
                row=cur.fetchone()
                if not row: raise ValueError("Unknown approved source or plant: "+o["scientific_name"])
                cur.execute("""
                  INSERT INTO horticulture.plant_merchant_offer
                   (plant_id,data_source_id,external_offer_id,product_url,price_amount,currency,
                    pot_size_l,height_cm,available,raw_payload)
                  VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                  ON CONFLICT (data_source_id,external_offer_id) DO UPDATE SET
                    price_amount=EXCLUDED.price_amount,currency=EXCLUDED.currency,
                    pot_size_l=EXCLUDED.pot_size_l,height_cm=EXCLUDED.height_cm,
                    available=EXCLUDED.available,observed_at=now(),raw_payload=EXCLUDED.raw_payload
                """,(row[1],row[0],o["external_offer_id"],o.get("product_url"),
                     o["price_amount"],o.get("currency","EUR"),o.get("pot_size_l") or None,
                     o.get("height_cm") or None,o.get("available"),
                     json.dumps(o,ensure_ascii=False)))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("json_file",type=Path)
    p.add_argument("--apply",action="store_true")
    args=p.parse_args()
    offers=json.loads(args.json_file.read_text(encoding="utf-8"))
    print(f"{len(offers)} offers; dry-run={not args.apply}")
    if not args.apply: return
    dsn=os.environ.get("GARDNAIZE_ML_DATABASE_URL")
    if not dsn: raise SystemExit("GARDNAIZE_ML_DATABASE_URL required")
    import psycopg
    with psycopg.connect(dsn) as conn: import_offers(conn,offers)

if __name__=="__main__":main()
