# GDAI-BACK validated photo and localized questionnaire

## Architecture boundary

- GDAI-FRONT **Node.js server** (not Angular browser) must save the confirmed image temporarily under `logs/images-upload/`, with a generated safe filename. **This Node.js server does not exist in the current production frontend image**: the current Dockerfile builds with Node and serves with Nginx. Implement the server and persistent volume separately.
- After confirmation, the trusted frontend server sends the photo and description to GDAI-BACK `POST /api/v1/gardens/photos/confirm`. GDAI-BACK calls GDAI-VALID ResNet-18 before inserting a validated photo into PostgreSQL. Invalid photos are never inserted.
- The current GDAI-VALID endpoint is an **assumed contract**: `POST ${VALIDATION_BASE_URL}/validate` multipart field `photo` -> `{"status":"VALID"|"INVALID","message":"..."}`. Align it with the actual model service.
- `GET /api/v1/gardens/photos/{photoId}/questions?language=fr&continent=EU&climate=TEMPERATE&country=FR` returns translated, filtered questions. `POST /api/v1/gardens/photos/{photoId}/answers` accepts `{"answers":{"location":"Paris","exposure":"FULL_SUN",...}}` with the same query parameters.
- The frontend should display 'Photo valide' only after a successful backend response; wait 2 seconds before showing a read-only photo/description alongside the questionnaire.
- Climate, continent and country are currently passed as request parameters. They should eventually come from validated location/climate metadata rather than being trusted as arbitrary user claims.
- Question `feature_key` is stable for Random Forest feature mapping. Question options and translations are normalized; `gdai_question_rules` permits multiple matching climate/geography rules. Global questions have no rules. Seed contains 8 global questions plus one extra for HOT_DRY climates.
- Images are stored in PostgreSQL `BYTEA` per the requested scope; large-scale deployment may prefer object storage and metadata-only database records.

## Integration blockers / security

1. Existing Angular PR #27 uses different endpoints and a different order (upload before model validation). Update the frontend and Node server together before merging.
2. Add authentication/authorization between the Node upload server and GDAI-BACK and protect access to photo IDs. The new controller is not yet access-controlled.
3. Validate file signatures and fully decode images server-side before production. Current code checks basic file signatures, size and ResNet-18 response.
4. Define cleanup/retention for temporary Node uploads, avoid storing binaries in log output, and use a private writable directory/volume.
5. Tests and Maven build have not been run. Verify Flyway version ordering against all migrations and align actual GDAI-VALID REST contract.
6. Answers are persisted for GDAI-PLANT to consume; invoking Random Forest is a separate integration step.
