"""Conservative, explainable fallback recommender. No synthetic ML labels."""
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Candidate:
    plant_id: int
    scientific_name: str
    minimum_hardiness_c: Optional[float] = None
    is_evergreen: Optional[bool] = None
    is_drought_tolerant: Optional[bool] = None
    maximum_height_cm: Optional[int] = None
    sun_exposures: tuple = ()
    quality_status: str = 'PENDING'


def rank(garden: dict, plants: list[Candidate], limit: int = 5, allow_pending: bool = False):
    """Return only compatible, evidence-backed candidates; never fill to five by guessing."""
    if not 1 <= limit <= 20:
        raise ValueError('limit must be between 1 and 20')
    results = []
    for p in plants:
        if p.quality_status != 'VALIDATED' and not allow_pending:
            continue
        reasons, warnings, score, checks = [], [], 0, 0
        winter = garden.get('minimum_winter_temperature_c')
        if winter is not None:
            if p.minimum_hardiness_c is not None:
                checks += 1
                if float(winter) < float(p.minimum_hardiness_c):
                    continue
                score += 3
                reasons.append('WINTER_HARDINESS_COMPATIBLE')
            else:
                warnings.append('HARDINESS_UNKNOWN')
        sun = garden.get('sun_exposure')
        if sun:
            if p.sun_exposures:
                checks += 1
                if sun not in p.sun_exposures:
                    continue
                score += 3
                reasons.append('SUN_EXPOSURE_COMPATIBLE')
            else:
                warnings.append('SUN_EXPOSURE_UNKNOWN')
        if garden.get('water_availability') == 'LOW':
            if p.is_drought_tolerant is True:
                checks += 1
                score += 2
                reasons.append('DROUGHT_TOLERANT')
            elif p.is_drought_tolerant is False:
                continue
            else:
                warnings.append('DROUGHT_TOLERANCE_UNKNOWN')
        if garden.get('evergreen_preferred') is True:
            if p.is_evergreen is True:
                checks += 1
                score += 1
                reasons.append('EVERGREEN')
            elif p.is_evergreen is None:
                warnings.append('EVERGREEN_UNKNOWN')
        height = garden.get('maximum_height_cm')
        if height is not None:
            if p.maximum_height_cm is not None:
                checks += 1
                if p.maximum_height_cm > height:
                    continue
                score += 1
                reasons.append('HEIGHT_COMPATIBLE')
            else:
                warnings.append('HEIGHT_UNKNOWN')
        if checks == 0:
            continue  # No positive evidence for suitability
        if p.quality_status != 'VALIDATED':
            warnings.append('PENDING_REVIEW_DEMO_ONLY')
        results.append({'plant_id': p.plant_id, 'scientific_name': p.scientific_name,
                        'score': score, 'reasons': reasons, 'warnings': warnings,
                        'quality_status': p.quality_status})
    results.sort(key=lambda x: (-x['score'], len(x['warnings']), x['scientific_name'].casefold(), x['plant_id']))
    return results[:limit]


def load_candidates(dsn: str) -> list[Candidate]:
    """Read only canonical traits and consolidated associations, never raw RHS evidence."""
    import psycopg
    from psycopg.rows import dict_row
    query = '''
    SELECT p.plant_id, p.scientific_name, p.minimum_hardiness_c,
           p.is_evergreen, p.is_drought_tolerant, p.maximum_height_cm,
           p.quality_status,
           COALESCE(array_agg(DISTINCT s.code) FILTER (WHERE s.code IS NOT NULL), '{}') AS sun_exposures
    FROM horticulture.plant p
    LEFT JOIN horticulture.plant_sun_exposure pse ON pse.plant_id=p.plant_id
         AND pse.suitability IN ('SUITABLE','PREFERRED')
    LEFT JOIN horticulture.sun_exposure s ON s.sun_exposure_id=pse.sun_exposure_id
    GROUP BY p.plant_id, p.scientific_name, p.minimum_hardiness_c,
             p.is_evergreen, p.is_drought_tolerant, p.maximum_height_cm, p.quality_status
    ORDER BY p.plant_id
    '''
    with psycopg.connect(dsn) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query)
            return [Candidate(**{**row, 'sun_exposures': tuple(row['sun_exposures'])}) for row in cur.fetchall()]
