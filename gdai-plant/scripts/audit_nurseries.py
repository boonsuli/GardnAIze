#!/usr/bin/env python3
import argparse,csv
from collections import Counter
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--file',default='gdai-plant/data/sources/mvp40-nursery-evidence.csv');a=p.parse_args()
with Path(a.file).open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
assert len(rows)==10, f'Expected 10 rows, got {len(rows)}'
assert len({r['scientific_name'] for r in rows})==10, 'Duplicate species'
print('Species:',len(rows))
print('Status:',dict(Counter(r['verification_status'] for r in rows)))
print('Evidence:',dict(Counter(r['evidence_type'] for r in rows)))
for r in rows: print(r['scientific_name'],':',r['verification_status'],r['evidence_type'])
print('No stock or purchase availability verified.')
