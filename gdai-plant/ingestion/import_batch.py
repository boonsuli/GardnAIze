"""Chunked, restartable catalog import reusing the audited V1 importer."""
import argparse
import json
import os
from pathlib import Path

from import_plants import parse_catalog, write_db, verified_species


def chunks(rows, size):
    if size < 1:
        raise ValueError('batch size must be positive')
    for i in range(0, len(rows), size):
        yield rows[i:i + size]


def run(catalog, report, batch_size=30, online=False, apply=False, dsn=None):
    parsed = parse_catalog(catalog)  # validates duplicates across entire catalog
    if apply and not dsn:
        raise ValueError('--apply requires GDAI_PLANT_DSN or --dsn')
    report_path = Path(report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    totals = {'total': len(parsed), 'processed': 0, 'verified': 0, 'review_required': 0, 'batches': 0, 'applied': bool(apply)}
    # NDJSON report allows review of partial progress on interrupted imports.
    with report_path.open('w', encoding='utf-8') as out:
        for batch in chunks(parsed, batch_size):
            # Reuse existing preparation/GBIF logic on a temporary JSON batch.
            # Instead of serializing batch, prepare individual rows using existing helpers.
            from import_plants import gbif_match
            import time
            prepared = []
            for row in batch:
                item = dict(row)
                item['gbif'] = None
                item['review_reason'] = 'TAXONOMY_NOT_CHECKED'
                if online:
                    try:
                        item['gbif'] = gbif_match(row['scientific_name'])
                        item['review_reason'] = 'TAXONOMY_MATCHED' if verified_species(item) else 'TAXONOMY_REVIEW_REQUIRED'
                    except Exception as exc:
                        item['review_reason'] = 'GBIF_LOOKUP_FAILED'
                        item['lookup_error'] = str(exc)
                    time.sleep(0.12)
                prepared.append(item)
                out.write(json.dumps(item, ensure_ascii=False) + '\n')
                out.flush()
            if apply:
                write_db(prepared, dsn)  # transaction per batch; safe rerun via ON CONFLICT
            totals['batches'] += 1
            totals['processed'] += len(prepared)
            totals['verified'] += sum(verified_species(r) for r in prepared)
            totals['review_required'] += sum(r['review_reason'] != 'TAXONOMY_MATCHED' for r in prepared)
            print(f"batch {totals['batches']}: {totals['processed']}/{totals['total']} processed")
    return totals


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog', required=True)
    p.add_argument('--report', default='/tmp/gdai-plant-batch.ndjson')
    p.add_argument('--batch-size', type=int, default=30)
    p.add_argument('--online', action='store_true')
    p.add_argument('--apply', action='store_true')
    p.add_argument('--dsn')
    a = p.parse_args()
    try:
        print(json.dumps(run(a.catalog, a.report, a.batch_size, a.online, a.apply,
                             a.dsn or os.getenv('GDAI_PLANT_DSN')), indent=2))
    except (ValueError, OSError) as exc:
        p.error(str(exc))


if __name__ == '__main__':
    main()
