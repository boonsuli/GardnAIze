# GDAI-PLANT V1 — conservative recommendation engine

Copy `api/recommendation_engine.py` and `tests/test_recommendation_engine.py` into `gdai-plant/`.

Run from repository root:

```bash
PYTHONPATH=gdai-plant gdai-plant/.venv/bin/python -m unittest discover -s gdai-plant/tests -p 'test_recommendation_engine.py' -v
```

## FastAPI adapter (add to existing api/main.py; do not replace its schemas)

```python
import os
from fastapi import HTTPException
from api.recommendation_engine import load_candidates, rank

# Inside the EXISTING /v1/recommendations handler, after Pydantic validation:
# dsn = os.getenv('GDAI_PLANT_DSN')
# if not dsn: raise HTTPException(status_code=503, detail='PLANT_DB_NOT_CONFIGURED')
# plants = load_candidates(dsn)
# selected = rank(request.garden.model_dump(exclude_none=True), plants, limit=request.limit)
# return {
#   'request_id': request.request_id,
#   'status': 'COMPLETED' if len(selected) == request.limit else 'INSUFFICIENT_DATA',
#   'recommendations': selected,
#   'model_version': 'rules-v1',
#   'warnings': [] if len(selected) == request.limit else ['Fewer than requested evidence-backed plants'],
# }
```

NOTE: The existing FastAPI response model may reject additional fields or statuses; align it explicitly with the contract before enabling. Keep `allow_pending=False` for real recommendations. Use `allow_pending=True` only for explicitly labelled demo diagnostics, never production.

No Random Forest model is claimed or loaded. No raw unlicensed RHS evidence is used.
