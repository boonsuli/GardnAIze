# GardnAIze — AI service

<p align="left">
  <img alt="Language: Python" src="https://img.shields.io/badge/Language-Python-3776AB" />
  <img alt="API: FastAPI" src="https://img.shields.io/badge/API-FastAPI-009688" />
  <img alt="ML: Random Forest target" src="https://img.shields.io/badge/ML-Random%20Forest%20target-228B22" />
  <img alt="Classification: KNN" src="https://img.shields.io/badge/Classification-KNN-3776AB" />
  <img alt="Clustering: K-Means" src="https://img.shields.io/badge/Clustering-K--Means-3776AB" />
  <img alt="Deployment: Docker" src="https://img.shields.io/badge/Deployment-Docker-2496ED" />
  <img alt="Vision: Gemini 3.8 Flash" src="https://img.shields.io/badge/Vision-Gemini%203.8%20Flash-4285F4" />
</p>

[Wiki de démarrage local](../docs/WIKI.md)

This Python/FastAPI service provides an API foundation for GardnAIze AI experiments and demonstration recommendations.

## AI ecosystem

- **GDAI-VALID:** ResNet-18 photo validation (segmentation belongs to optional GDAI-SEGMT), documented separately in [validation](../validation/).
- **GDAI-VISION:** Gemini Vision garden-photo analysis (`gemini-3.8-flash`, runtime-configurable).
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
