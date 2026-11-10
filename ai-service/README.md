# GardnAIze AI Service

> **Point E2E — 10/11/2026 :** le service FastAPI fournit une base opérationnelle et des recommandations de démonstration par règles. Le service d'inférence ResNet-18 et ses poids entraînés, l'intégration des observations Gemini et le moteur Random Forest réel restent à raccorder et à tester. Exposer des contrats Python privés consommés par GDAI-BACK, avec schémas, erreurs et versions de modèle ; ne pas présenter les règles de démo comme des prédictions ML. [Plan de câblage](../docs/E2E_READINESS_2026-11-10.md).

Python **3.12** and **FastAPI** provide an independent inference API.

**Current implementation:** a working FastAPI scaffold with `/`, `/health`, and interactive OpenAPI documentation at `/docs`. Plant ranking, image classification, model loading and ML/DL inference are planned; no trained models are bundled.

## Docker

From the repository root:

```bash
docker compose up --build -d
docker compose logs -f ai-service
```

Open http://localhost:8000/docs or check http://localhost:8000/health.

Run the AI service alone:

```bash
docker build -t gardnaize-ai ./ai-service
docker run --rm -p 127.0.0.1:8000:8000 -e LOG_LEVEL=DEBUG gardnaize-ai
```

## Local Python development

```bash
cd ai-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Logs and security

The standard Python `logging` module writes to stdout/stderr. Set `AI_LOG_LEVEL=DEBUG` in Compose (or `LOG_LEVEL=DEBUG` when running the container directly). Supported Python levels: DEBUG, INFO, WARNING, ERROR, CRITICAL. Avoid logging photos, credentials or personal data.

The image uses a non-root user and installs only minimal API dependencies. Future ML/DL inference requirements will be added when the corresponding models and endpoints are implemented. In Compose the API port is published on localhost only; do not expose it publicly without authentication, rate limiting and network controls.

## Automated tests

Run `pip install -r requirements-dev.txt` and `python -m pytest -q tests`. CI runs these unit tests before building and smoke-testing the Docker image. Source files use four-space indentation and no tabs.

## Backend orchestration

Java sends `POST /recommendations` with location, exposure and soil type. This currently returns exactly three **demo rule-based** plants (`mode: demo-rules-not-ai`); no trained model is used. Python tests verify the request contract and validation.
