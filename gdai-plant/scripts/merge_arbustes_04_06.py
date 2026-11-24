#!/usr/bin/env python3
"""Merge documentary observations for shrubs 4–6 without overwriting existing evidence."""
import argparse
import csv
import shutil
from datetime import datetime
from pathlib import Path

MAPPING = {
    'sun_exposure': ('sun_exposure', 'observed_value'),
    'drainage': ('soil_drainage', 'observed_value'),
    'hardiness_rhs': ('hardiness_min_c', 'original_range'),
    'height_range': ('height_cm', 'original_range'),
    'spread_range': ('spread_cm', 'original_range'),
    'evergreen': ('evergreen', 'observed_value'),
}

def load(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='gdai-plant/data/sources/mvp40-required-traits-batch01.csv')
    parser.add_argument('--research', default='../gdai-mvp40-arbustes-04-06-research.csv')
    args = parser.parse_args()
    base, research = Path(args.base), Path(args.research)
    columns, rows = load(base)
    _, incoming = load(research)
    index = {(r['scientific_name'].strip(), r['field'].strip()): r for r in rows}
    if len(rows) != 70 or len(index) != 70:
        raise SystemExit('ERROR: expected 70 unique destination keys; no modification')
    changes, skips, errors = [], [], []
    for r in incoming:
        source_field = r['trait'].strip()
        if source_field not in MAPPING:
            errors.append(f'Unknown trait: {source_field}'); continue
        field, dest_col = MAPPING[source_field]
        key = (r['scientific_name'].strip(), field)
        if key not in index:
            errors.append(f'Missing key: {key}'); continue
        target = index[key]
        if target['review_status'] not in ('TO_RESEARCH', 'RESEARCH_ONLY'):
            skips.append((key, 'protected status')); continue
        if target['observed_value'].strip() or target['original_range'].strip():
            skips.append((key, 'already documented')); continue
        value = r['observed_value'].strip()
        if not value:
            skips.append((key, 'empty research')); continue
        if source_field == 'sun_exposure':
            value = value.replace('FULL_SUN', 'SUN')
        if source_field in ('height_range', 'spread_range'):
            value = value.replace(' m', ' m')  # preserve source units; do not convert to scalar cm
        if source_field == 'hardiness_rhs':
            value = 'RHS ' + value  # not a Celsius threshold
        target[dest_col] = value
        target['source_url'] = r['source_url'].strip()
        target['source_license'] = 'UNKNOWN'
        target['commercial_reuse_allowed'] = 'false'
        target['review_status'] = 'RESEARCH_ONLY'
        target['notes'] = (r.get('note') or 'Documentary research; review required').strip()
        changes.append((key, dest_col, value))
    if errors:
        print('\n'.join(errors))
        raise SystemExit('ERROR: source mismatch; no file written')
    print('Planned updates:', len(changes), 'Already filled/skipped:', len(skips))
    for key, col, value in changes:
        print('  ', key, col, '=', value)
    if not changes:
        print('Nothing to change.'); return
    backup = base.with_name(base.stem + '.before-04-06-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.csv')
    shutil.copy2(base, backup)
    temp = base.with_suffix('.tmp')
    with temp.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader(); writer.writerows(rows)
    temp.replace(base)
    print('Backup:', backup)
    print('Final rows:', len(rows))

if __name__ == '__main__':
    main()
