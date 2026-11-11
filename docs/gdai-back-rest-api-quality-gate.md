# GDAI-BACK REST API quality gate

All GDAI-BACK endpoints and photo-workflow endpoints must be documented in English using OpenAPI 3 annotations and verified against the generated contract.

Required endpoints when this branch is integrated with the current backend:
- OpenAPI JSON: `GET /v3/api-docs`
- Swagger UI: `GET /swagger-ui.html`
- ReDoc: `GET /redoc.html` (implemented in PR #35; do not duplicate this viewer in this branch)
- Health: `GET /actuator/health`

The photo-workflow API must document multipart fields, success responses, invalid-photo status, provider-unavailable errors and asynchronous polling. Confirm real GDAI-VALID and GDAI-VISION request/response contracts before merging. This branch has not yet been reconciled with PR #35; avoid merging competing photo controllers or database migrations without a conflict review.
