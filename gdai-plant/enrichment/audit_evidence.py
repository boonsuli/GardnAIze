"""Read-only preflight for a curated horticultural evidence manifest."""
import argparse
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_TYPES = {'OBSERVED', 'EXPERT_REVIEWED'}

def audit(rows):
    if not isinstance(rows, list):
        raise ValueError('Manifest must be an array')
    keys = set()
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f'Row {index}: expected object')
        for field in ('scientific_name', 'source_name', 'source_url', 'attribute_name', 'value', 'evidence_type'):
            if field not in row or row[field] is None or row[field] == '':
                raise ValueError(f'Row {index}: missing {field}')
        url = urlparse(row['source_url'])
        if url.scheme != 'https' or not url.netloc:
            raise ValueError(f'Row {index}: invalid HTTPS source URL')
        if row['evidence_type'] not in ALLOWED_TYPES:
            raise ValueError(f'Row {index}: unsupported evidence type')
        key = (row['scientific_name'].casefold().strip(), row['source_name'], row['source_url'], row['attribute_name'], json.dumps(row['value'], sort_keys=True, ensure_ascii=False))
        if key in keys:
            raise ValueError(f'Row {index}: duplicate fact')
        keys.add(key)
    print(f'Valid facts: {len(rows)}')
    print('Plants:', dict(Counter(r['scientific_name'] for r in rows)))
    print('Sources:', dict(Counter(r['source_name'] for r in rows)))
    print('Attributes:', dict(Counter(r['attribute_name'] for r in rows)))
    print('Preflight only; no database changes')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--manifest', required=True)
    args = p.parse_args()
    audit(json.loads(Path(args.manifest).read_text(encoding='utf-8')))
