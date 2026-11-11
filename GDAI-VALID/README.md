# GDAI-VALID — FastAPI / ResNet-18

Independent garden photo validation API. No weights are bundled and the service never predicts using random weights.

## Development

```bash
cd GDAI-VALID
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
pytest -q
```

Swagger: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
OpenAPI: http://localhost:8000/openapi.json

## Contract

- POST /api/v1/validation/photo: multipart photo (JPEG, PNG, WebP), optional description (max 1000 characters), optional request_id.
- GET /api/v1/health: process status and model readiness.
- GET /api/v1/model/info: model metadata.

Returns HTTP 200 with valid true/false for model decisions; 413/415/422 for invalid uploads; 503 if model weights are unavailable. Default maximum size: 5 MiB, configurable with VALID_MAX_IMAGE_BYTES.

## Future retraining and Alyra Block 5 deployment

Retrain using a larger labeled dataset. Export a trusted ResNet-18 state_dict to /models/garden_resnet18.pt and metadata to /models/metadata.json. Override with VALID_MODEL_PATH and VALID_METADATA_PATH. Metadata includes ordered classes, model version, preprocessing normalization and threshold. Match these to the actual training pipeline before deployment. Validate independent holdout metrics and document provenance, packaging, registry, deployment, monitoring and rollback.

Build: docker build -t gdai-valid .
The service is not yet connected to Spring Boot or root Compose. Model packaging and actual deployment will follow in a later phase.
