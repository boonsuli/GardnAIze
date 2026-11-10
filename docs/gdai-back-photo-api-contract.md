# GDAI-BACK — Photo workflow contract (draft v1)

## Public API (Swagger)

Existing springdoc dependency: `springdoc-openapi-starter-webmvc-ui:2.8.13`.
Run backend, then open `/swagger-ui.html` or `/v3/api-docs`.

### POST /api/v1/gardens/photos
Multipart fields: `photo` (JPEG/PNG, max 1 MiB), `description` (required, max 2000 chars).

- 202: `{"id":"<uuid>","status":"VISION_PENDING","message":"Photo valide","valid":true}`
- 422: `{"id":null,"status":"INVALID","message":"Photo non valide","valid":false}`
- 400: invalid input; `{"code":"INVALID_UPLOAD","message":"..."}`
- 503: classifier unavailable/incompatible; `{"code":"UPSTREAM_UNAVAILABLE","message":"..."}`

### GET /api/v1/gardens/photos/{id}
`{"id":"<uuid>","status":"VISION_PENDING|VISION_COMPLETED|VISION_FAILED","message":"..."}`

### GET /api/v1/gardens/photos/{id}/vision
`{"id":"<uuid>","status":"VISION_COMPLETED","analysisJson":"{...}"}`.
The JSON is currently returned as a serialized string, not a normalized vision DTO.

## Internal contracts requiring alignment

The GDAI-VALID endpoint is configurable via `gardnaize.photo.valid-url`
(default `http://localhost:8000/classify-garden`). The current Java client sends raw
JPEG/PNG bytes with the image media type, and expects `{"valid":true|false}`.
**This is a proposed adapter contract, not proof that the Python endpoint exists.**
If FastAPI expects multipart or a different JSON shape, adapt the Java client before merging.

The GDAI-VISION endpoint is configurable via `gardnaize.photo.vision-url`
(default `http://localhost:8000/analyze`). The Java client currently sends raw
image bytes and expects JSON. Its request and response must be reconciled with
the existing Gemini integration before merging.

## Processing rules

- FRONT sends the photo once after user confirmation.
- BACK invokes VALID synchronously. On rejection, return 422; do not persist.
- On acceptance, BACK stores photo + description in PostgreSQL and returns 202.
- Vision runs in a bounded local executor; FRONT polls status.
- If VALID is unavailable or returns an unexpected schema, return 503 (fail closed).
- A failed Vision request marks `VISION_FAILED`; it does not invalidate the accepted photo.

## Merge gates

1. Verify application component scan includes `com.gardnaize.photo`.
2. Verify Flyway migration ordering against the existing schema.
3. Align both Python API contracts (media types, payloads, error handling).
4. Run `cd backend && mvn test`, Swagger smoke test, and PostgreSQL integration tests.
5. Test JPEG/PNG success, rejection, invalid media type, oversize upload, timeout,
   missing photo, failed Vision, and retry policy.
6. Review photo retention, upload content inspection, filename sanitization,
   access control, executor shutdown, and production persistence strategy.
7. Align FRONT handling of 202/422/400/503 and the status bar.

**This PR is intentionally a draft until integration and tests pass.**
