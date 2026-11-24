"""GDAI-PLANT: read-only catalog/evidence API; RF integration is intentionally gated."""
import os
from typing import Any

import psycopg
from fastapi import APIRouter, FastAPI, HTTPException, Query
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

MVP_ATTRIBUTES = (
    'sun_exposure', 'water_need', 'soil_drainage', 'height_cm',
    'spread_cm', 'evergreen', 'hardiness_min_c',
)

router = APIRouter(prefix='/v1', tags=['GDAI-PLANT'])


def fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    dsn = os.getenv('GARDNAIZE_ML_DATABASE_URL')
    if not dsn:
        raise HTTPException(503, 'GARDNAIZE_ML_DATABASE_URL is not configured')
    try:
        with psycopg.connect(dsn, row_factory=dict_row, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute('SET TRANSACTION READ ONLY')
                cur.execute(sql, params)
                return list(cur.fetchall())
    except psycopg.Error:
        raise HTTPException(503, 'Horticultural database unavailable') from None


@router.get('/health')
def health():
    fetch_all('SELECT 1 AS ok')
    return {'service': 'GDAI-PLANT', 'status': 'ok', 'database': 'connected'}


@router.get('/attributes')
def attributes():
    """Declared matching contract; coverage is measured, not assumed."""
    rows = fetch_all('''
        SELECT e.attribute_name, COUNT(DISTINCT e.plant_id) AS plants_covered,
               COUNT(*) AS evidence_count
        FROM horticulture.plant_attribute_evidence e
        WHERE e.attribute_name = ANY(%s)
        GROUP BY e.attribute_name
    ''', (list(MVP_ATTRIBUTES),))
    coverage = {r['attribute_name']: r for r in rows}
    return {
        'attributes': [
            {'name': name,
             'plants_covered': coverage.get(name, {}).get('plants_covered', 0),
             'evidence_count': coverage.get(name, {}).get('evidence_count', 0)}
            for name in MVP_ATTRIBUTES
        ],
        'note': 'Coverage indicates presence only, not horticultural validation.',
    }


@router.get('/plants')
def plants(limit: int = Query(40, ge=1, le=100), offset: int = Query(0, ge=0)):
    return fetch_all('''
        SELECT p.plant_id, p.scientific_name, p.quality_status,
               p.ready_for_matching,
               COUNT(e.plant_attribute_evidence_id) FILTER
                 (WHERE e.attribute_name = ANY(%s)) AS mvp_evidence_count,
               COUNT(DISTINCT e.attribute_name) FILTER
                 (WHERE e.attribute_name = ANY(%s)) AS mvp_attributes_covered
        FROM horticulture.plant p
        LEFT JOIN horticulture.plant_attribute_evidence e ON e.plant_id = p.plant_id
        GROUP BY p.plant_id, p.scientific_name, p.quality_status, p.ready_for_matching
        ORDER BY p.scientific_name, p.plant_id
        LIMIT %s OFFSET %s
    ''', (list(MVP_ATTRIBUTES), list(MVP_ATTRIBUTES), limit, offset))


@router.get('/plants/{plant_id}/evidence')
def plant_evidence(plant_id: int):
    found = fetch_all('SELECT plant_id FROM horticulture.plant WHERE plant_id=%s', (plant_id,))
    if not found:
        raise HTTPException(404, 'Plant not found')
    return fetch_all('''
        SELECT plant_attribute_evidence_id, attribute_name, value_as_reported,
               evidence_type, recorded_at, data_source_id, source_record_id
        FROM horticulture.plant_attribute_evidence
        WHERE plant_id=%s AND attribute_name = ANY(%s)
        ORDER BY attribute_name, plant_attribute_evidence_id
    ''', (plant_id, list(MVP_ATTRIBUTES)))


@router.get('/readiness')
def readiness():
    rows = fetch_all('''
        SELECT quality_status, ready_for_matching, COUNT(*) AS plants
        FROM horticulture.plant
        GROUP BY quality_status, ready_for_matching
        ORDER BY quality_status, ready_for_matching
    ''')
    return {'groups': rows, 'note': 'Imported evidence does not imply matching readiness.'}


class RecommendationRequest(BaseModel):
    garden_id: str | None = None
    preferences: dict[str, Any] = Field(default_factory=dict)


@router.post('/recommendations')
def recommendations(request: RecommendationRequest):
    # No fake predictions: the actual RF adapter and its training data are pending.
    ready = fetch_all('SELECT COUNT(*) AS n FROM horticulture.plant WHERE ready_for_matching = true')
    if ready[0]['n'] < 5:
        raise HTTPException(409, 'Fewer than five plants are ready for matching')
    raise HTTPException(501, 'Random Forest adapter is not connected')


def create_app() -> FastAPI:
    application = FastAPI(title='GDAI-PLANT horticultural API', version='0.2.0')
    application.include_router(router)
    return application


app = create_app()
