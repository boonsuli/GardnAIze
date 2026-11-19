# Photo → validation → questionnaire → consent → vision (PR #35)

## Frontend dictionaries
- `/i18n/GardnAIze_data_FR.json`
- `/i18n/GardnAIze_data_EN.json`
The backend returns **keys and option values only** from `GET /api/v1/questionnaire`. No localized wording crosses REST.

## Implemented calls
1. User confirms photo and location; frontend POSTs `file` to `/api/v1/photos/validate`. The backend calls GDAI-VALID `/validate` without persistence or Gemini.
2. On `{ "valid": true }`, frontend loads the questionnaire catalog and localized JSON; mandatory answers must be completed.
3. User sees the localized external processing notice. Refusal resets frontend workflow and no vision upload is sent.
4. Acceptance triggers `POST /api/v1/gardens`, then multipart `POST /api/v1/gardens/{gardenId}/photos` with fields `file`, `description`, `answersJson` and `consentKey=privacy.externalProcessingNotice`.
5. Backend requires the consent key, persists photo and answers/consent audit in `public.garden_photo_questionnaire` (Flyway V13), then invokes external vision when configured.

## Verification blockers
- **GDAI-VALID adapter contract is assumed**: `POST /validate` multipart `file`, response `{ "valid": boolean, "reason": string }`. Confirm against the actual Python service before merging.
- The upload endpoint trusts prior frontend validation; it does not cryptographically bind validation to the uploaded bytes. Server-side revalidation or a signed, expiring validation token is required before production.
- Legacy `GardenPhotoService.upload(...)` overload is retained for compatibility tests. Audit and remove legacy no-consent entry points before production.
- Backend currently invokes vision synchronously. Add asynchronous status handling/retries separately.
- Verify WebP support, migration V13, Maven tests, Angular build and integration tests in CI.

## Architecture boundary
GDAI-FRONT communicates **only** with GDAI-BACK. It does not know or invoke GDAI-VALID, Gemini, or GDAI-PLANT. Angular HttpClient is non-blocking, but the current backend upload is still a synchronous processing request; a true `202 Accepted` background orchestration with status polling is not implemented yet.

## Safety regression tests
`GardenPhotoServiceTest` checks refusal/missing consent, wrong consent key, malformed answers and missing required answers: all must fail **before** any JDBC interaction. `PhotoValidationServiceTest` checks the real downstream adapter. These tests must pass in CI before merge.
