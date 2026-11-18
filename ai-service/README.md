# GardnAIze — AI service

![Python](https://img.shields.io/badge/Python-3.12-3776AB) ![API](https://img.shields.io/badge/API-FastAPI-009688) ![ML](https://img.shields.io/badge/ML-Random%20Forest%20target-228B22) ![Research](https://img.shields.io/badge/Research-KNN%20%2B%20K----Means-3776AB)

This Python/FastAPI service provides an API foundation for GardnAIze AI experiments and demonstration recommendations.

## AI ecosystem

- **GDAI-VALID:** ResNet-18 photo validation and intended local garden segmentation, documented separately in [validation](../validation/).
- **GDAI-VISION:** optional external Gemini Vision observations.
- **GDAI-PLANT:** target Random Forest engine combining garden characteristics, user preferences and horticultural plant attributes.
- **KNN / K-Means:** supervised classification and unsupervised clustering experiments documented in [notebooks](../notebooks/).
- **GDAI-GNERAT:** optional image visualization after plant recommendations.

The existing `POST /recommendations` demo-rule response is **not** a trained Random Forest prediction. Model training, catalog integration and end-to-end serving must be verified independently.

## Local development

```bash
cd ai-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q tests
uvicorn app.main:app --reload
```

OpenAPI: http://localhost:8000/docs. Health: http://localhost:8000/health.

**E2E demonstration objective:** 15 December 2026.
