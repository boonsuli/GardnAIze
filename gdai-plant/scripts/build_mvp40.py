#!/usr/bin/env python3
"""Create a candidate horticultural shortlist and blank, auditable enrichment template.
No horticultural traits, supplier stock or rights are asserted by this script.
"""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
# Candidate list, NOT a validated inventory. Botanical names/cultivars require review.
GROUPS = {
 'SHRUB': [
  'Viburnum tinus', 'Photinia × fraseri', 'Choisya ternata', 'Elaeagnus × ebbingei',
  'Osmanthus heterophyllus', 'Pittosporum tenuifolium', 'Hydrangea paniculata',
  'Cornus alba', 'Spiraea japonica', 'Sarcococca confusa'],
 'PERENNIAL': [
  'Salvia nemorosa', 'Geranium macrorrhizum', 'Echinacea purpurea', 'Rudbeckia fulgida',
  'Nepeta × faassenii', 'Hylotelephium spectabile', 'Agapanthus africanus',
  'Helleborus orientalis', 'Heuchera villosa', 'Achillea millefolium'],
 'GRASS': [
  'Miscanthus sinensis', 'Calamagrostis × acutiflora', 'Panicum virgatum',
  'Stipa tenuissima', 'Pennisetum alopecuroides'],
 'GROUNDCOVER': [
  'Vinca minor', 'Ajuga reptans', 'Pachysandra terminalis',
  'Waldsteinia ternata', 'Thymus serpyllum'],
 'TREE': [
  'Amelanchier lamarckii', 'Acer campestre', 'Carpinus betulus',
  'Cercis siliquastrum', 'Malus floribunda'],
 'CLIMBER': [
  'Clematis armandii', 'Lonicera periclymenum', 'Trachelospermum jasminoides',
  'Hedera helix', 'Wisteria sinensis'],
}
FIELDS = [
 'scientific_name','plant_type','sun_exposure','soil_type','soil_drainage',
 'water_need','hardiness_min_c','height_cm','spread_cm','evergreen',
 'flower_color','flowering_months','maintenance_level','heat_tolerance',
 'drought_tolerance','nursery_name','nursery_country','nursery_product_url',
 'nursery_observed_at','source_url','source_license','commercial_reuse_allowed',
 'reviewer','reviewed_at','quality_status'
]

def build():
    rows = [{'scientific_name': name, 'candidate_category': group,
             'selection_status': 'CANDIDATE', 'horticultural_validation': 'NOT_REVIEWED',
             'nursery_availability': 'NOT_VERIFIED'}
            for group, names in GROUPS.items() for name in names]
    assert len(rows) == 40, len(rows)
    assert len({r['scientific_name'].casefold() for r in rows}) == 40
    assert Counter(r['candidate_category'] for r in rows) == {
        'SHRUB': 10, 'PERENNIAL': 10, 'GRASS': 5,
        'GROUNDCOVER': 5, 'TREE': 5, 'CLIMBER': 5}
    DATA.mkdir(parents=True, exist_ok=True)
    path_json = DATA / 'plants-mvp-40.json'
    path_csv = DATA / 'plants-mvp-40-enriched.csv'
    path_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # Never overwrite hand-enriched data.
    if path_csv.exists():
        raise FileExistsError(f'{path_csv} exists; refusing to overwrite reviewed data')
    with path_csv.open('w', encoding='utf-8', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({'scientific_name': row['scientific_name'],
                             'plant_type': row['candidate_category'],
                             'quality_status': 'PENDING'})
    return path_json, path_csv

if __name__ == '__main__':
    for path in build():
        print('CREATED', path)
