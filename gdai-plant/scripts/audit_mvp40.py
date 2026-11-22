#!/usr/bin/env python3
"""Read-only audit of the 10-shrub research matrix; prepare missing-data queues."""
import csv
from collections import Counter
from pathlib import Path

ROOT = Path('gdai-plant/data/sources')
SRC = ROOT / 'mvp40-required-traits-batch01.csv'
FIELDS = ('sun_exposure','soil_drainage','water_need','hardiness_min_c','height_cm','spread_cm','evergreen')
with SRC.open(encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 70, f'Expected 70 rows, got {len(rows)}'
keys = [(r['scientific_name'], r['field']) for r in rows]
assert len(set(keys)) == 70, 'Duplicate (plant, field)'
assert all(r['field'] in FIELDS for r in rows), 'Unexpected field'
missing = [r for r in rows if not (r['observed_value'].strip() or r['original_range'].strip())]
print('Total:',len(rows),'observed values:',sum(bool(r['observed_value'].strip()) for r in rows),
      'ranges:',sum(bool(r['original_range'].strip()) for r in rows),
      'missing:',len(missing))
print('Missing by field:',dict(Counter(r['field'] for r in missing)))
print('Status:',dict(Counter(r['review_status'] for r in rows)))
for r in missing:
    print('TO_RESEARCH:',r['scientific_name'],'/',r['field'])
queue = ROOT / 'mvp40-missing-review.csv'
if queue.exists():
    print('PRESERVED existing',queue)
else:
    with queue.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['scientific_name','field','observed_value','original_range','source_url','source_license','commercial_reuse_allowed','reviewer','reviewed_at','review_status','notes'])
        w.writeheader();w.writerows(missing)
    print('CREATED',queue)
