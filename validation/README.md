# GDAI-VALID — Photo validation and garden segmentation

![API](https://img.shields.io/badge/API-FastAPI-009688) ![DL](https://img.shields.io/badge/DL-ResNet----18-EE4C2C) ![Segmentation](https://img.shields.io/badge/Segmentation-DeepLabV3%20candidate-7952B3) ![Runtime](https://img.shields.io/badge/Runtime-PyTorch-EE4C2C)

GDAI-VALID is a local Python/FastAPI service for interpreting garden photographs.

## AI functions

- **ResNet-18:** classify whether an uploaded image is suitable for garden analysis.
- **Semantic segmentation:** identify meaningful garden zones (such as lawn, paths, planting beds and built surfaces). DeepLabV3 is a candidate architecture; the final model and trained classes must be validated.
- **Structured output:** provide usable observations to GDAI-BACK, which orchestrates downstream plant recommendations.

The validation API exists, but trained model weights are not bundled in Git. Segmentation training and serving are not presented as completed. A pretrained model alone does not demonstrate project-specific fine-tuning.

## Development

```bash
cd validation
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
pytest -q
```

## Existing validation API

- `POST /api/v1/validation/photo`: JPEG, PNG or WebP validation, up to 5 MiB by default.
- `GET /api/v1/health`: service and model readiness.
- `GET /api/v1/model/info`: model metadata.

Swagger: http://localhost:8000/docs  
ReDoc: http://localhost:8000/redoc

The service returns 503 when required model weights are unavailable. No segmentation endpoint is asserted until implemented and tested.

**E2E demonstration objective:** 15 December 2026.
