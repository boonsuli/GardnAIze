# GardnAIze REST API documentation standard (English)

Every REST-exposing module must provide an English-language OpenAPI 3 contract, Swagger UI, ReDoc, a health endpoint and automated tests. Notebook-only modules do not expose an HTTP API and are exempt.

| Module | OpenAPI JSON | Swagger UI | ReDoc | Health |
| --- | --- | --- | --- | --- |
| GDAI-BACK (Spring Boot) | `/v3/api-docs` | `/swagger-ui.html` | `/redoc.html` | `/actuator/health` |
| GDAI-VALID (FastAPI) | `/openapi.json` | `/docs` | `/redoc` | `/api/v1/health` |

## Photo validation contract

Browser -> GDAI-BACK: `POST /api/v1/photos/validate` with multipart field `file`.
GDAI-BACK -> GDAI-VALID: `POST /api/v1/validation/photo` with multipart field `photo`.

GDAI-VALID responds with `request_id`, `valid`, `status` (`VALID` or `INVALID`), `confidence`, `predicted_class`, `model`, `reason_code`, and `message`. GDAI-BACK returns the validated response to the frontend. Unavailable model/service must not be interpreted as a valid photo.

The adapter is stateless and does not persist the image. **Important:** the current final photo upload is not yet cryptographically bound to this preflight check; the backend must revalidate the submitted bytes before treating a photo as validated.

The Spring Boot ReDoc viewer loads its JavaScript from the ReDoc CDN, so it requires browser network access. OpenAPI JSON and Swagger UI remain served by the backend.

## Verification

Run `mvn clean verify` in `backend/` with PostgreSQL available for integration tests. Check the OpenAPI JSON, both documentation viewers, and health endpoints when each service is running. GDAI-VALID model readiness is reported separately in its health response; an HTTP 200 alone does not prove the model weights are loaded.
