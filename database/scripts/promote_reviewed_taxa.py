"""Promote reviewed taxonomy staging into candidate catalogue, preserving provenance.

Taxonomic names are NOT evidence of outdoor suitability, hardiness, or gardening
traits. No images are downloaded. Existing curated plant fields are untouched.
Requires explicit licence id and commercial reuse authorization.
"""
import argparse,os,unicodedata,json

def key(name):
    return " ".join(unicodedata.normalize("NFKC",name).casefold().split())+" | "

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True,choices=["GBIF","WCVP","TELA_BOTANICA","MERCHANT_AUTHORIZED"])
    p.add_argument("--license-id",required=True)
    p.add_argument("--commercial-reuse-reviewed",action="store_true")
    p.add_argument("--limit",type=int,default=500)
    p.add_argument("--apply",action="store_true")
    a=p.parse_args()
    if not a.commercial_reuse_reviewed: p.error("Review source reuse rights before proceeding")
    if a.limit<1: p.error("--limit must be positive")
    import psycopg
    dsn=os.environ["GARDNAIZE_ML_DATABASE_URL"].replace("postgresql+psycopg://","postgresql://",1)
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT source_key,external_id,scientific_name,canonical_name,
                           source_url,source_version,payload
                           FROM horticulture.ml_taxon_source_staging
                           WHERE source_key=%s AND review_status='APPROVED'
                           ORDER BY external_id LIMIT %s""",(a.source,a.limit))
            rows=cur.fetchall()
        print(f"approved_taxa={len(rows)} source={a.source} apply={a.apply}")
        if not a.apply:return
        with conn.transaction():
            with conn.cursor() as cur:
                for source,ext,name,canonical,url,version,payload in rows:
                    # A synonym is not automatically equivalent to a canonical taxon:
                    # prefer a reviewed canonical_name if supplied; preserve original in payload.
                    target=(canonical or name).strip()
                    if not target: continue
                    cur.execute("""INSERT INTO horticulture.ml_plant_catalog
                        (scientific_name,canonical_key)
                        VALUES (%s,%s)
                        ON CONFLICT(canonical_key) DO UPDATE SET updated_at=now()
                        RETURNING plant_id""",(target,key(target)))
                    plant_id=cur.fetchone()[0]
                    cur.execute("""INSERT INTO horticulture.ml_plant_source_record
                        (source_key,external_id,plant_id,source_url,source_version,
                         license_id,commercial_reuse_allowed,payload)
                        VALUES (%s,%s,%s,%s,%s,%s,true,%s::jsonb)
                        ON CONFLICT(source_key,external_id) DO UPDATE SET
                          plant_id=EXCLUDED.plant_id,source_url=EXCLUDED.source_url,
                          source_version=EXCLUDED.source_version,
                          license_id=EXCLUDED.license_id,
                          payload=EXCLUDED.payload,retrieved_at=now()""",
                        (source,ext,plant_id,url,version,a.license_id,payload if isinstance(payload,str) else json.dumps(payload)))
        print("Committed taxonomy-only PENDING plants. Horticultural suitability remains unverified.")
if __name__=="__main__":main()
