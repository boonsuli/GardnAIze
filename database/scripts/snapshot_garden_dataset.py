"""Freeze an auditable snapshot of accepted, reviewed garden records.

Run only on an isolated ML database. Uses database-side SHA256 of metadata when
an image checksum has not been populated; metadata hashes do NOT prove image bytes.
"""
import argparse
import hashlib
import json
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-key", default="garden-curated")
    parser.add_argument("--version", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    import psycopg
    dsn = os.environ.get("GARDNAIZE_ML_DATABASE_URL")
    if not dsn:
        raise SystemExit("GARDNAIZE_ML_DATABASE_URL required")
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT image_id,source_key,external_id,image_uri,garden_group_key,
                                  dataset_split,image_sha256
                           FROM horticulture.garden_image_candidate
                           WHERE review_status='ACCEPTED' AND dataset_split IS NOT NULL
                           ORDER BY source_key,external_id""")
            rows = cur.fetchall()
            if not rows:
                raise SystemExit("No accepted garden records with dataset splits")
            items = []
            for image_id, source, external, uri, group, split, sha in rows:
                reference = f"{source}:{external}"
                # No silent claim that metadata checksum is the image checksum.
                fingerprint = sha.strip() if sha else hashlib.sha256(
                    json.dumps([source,external,uri,group,split],ensure_ascii=False).encode()
                ).hexdigest()
                items.append((image_id,split,reference,fingerprint))
            manifest = hashlib.sha256(json.dumps(items,sort_keys=True).encode()).hexdigest()
            print(f"items={len(items)} manifest_sha256={manifest} apply={args.apply}")
            if not args.apply:
                return
            cur.execute("""INSERT INTO horticulture.ml_dataset_version
                            (dataset_key,version_tag,purpose,status,frozen_at,manifest_sha256,notes)
                            VALUES (%s,%s,'GARDEN','FROZEN',now(),%s,%s)
                            RETURNING dataset_id""",
                        (args.dataset_key,args.version,manifest,
                         "Snapshot from accepted garden metadata; item hashes may be metadata-only"))
            dataset_id = cur.fetchone()[0]
            for image_id,split,reference,fingerprint in items:
                cur.execute("""INSERT INTO horticulture.ml_dataset_item
                               (dataset_id,item_kind,item_id,split,source_reference,content_sha256)
                               VALUES (%s,'GARDEN_IMAGE',%s,%s,%s,%s)""",
                            (dataset_id,image_id,split,reference,fingerprint))
        conn.commit()
        print(f"Frozen dataset_id={dataset_id}")

if __name__ == "__main__":
    main()
