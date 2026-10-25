# External photo analysis workflow (MVP)

## Scope
This backend implementation persists JPEG/PNG photos (max 10 MB) in PostgreSQL `BYTEA` before sending them to an external **adapter**. WebP is not supported in this MVP backend, even though the existing Angular file picker allows it. Minimum accepted dimensions are 640 × 480 pixels. This version performs synchronous requests (30-second provider read timeout); async jobs, retries, photo deletion, and object storage are follow-ups.

## Provider configuration
- `VISION_ENABLED=true` to enable provider calls (disabled by default).
- `VISION_BASE_URL=https://your-adapter.example` for an external adapter implementing `POST /analyze`.
- `VISION_API_KEY` for an optional bearer token (keep in environment/secret manager).
- `VISION_PROVIDER_NAME` for provenance.

The adapter is a provider-neutral contract, **not a native Gemini/Claude endpoint**. A dedicated adapter will be needed for the chosen vision provider.

Request JSON: `{photoId, mimeType, imageBase64, requirements: {gardenRequired: true, allowedClimateCodes: ["TEMPERATE_CONTINENTAL"], minimumWidthPx: 640, minimumHeightPx: 480}}`.

Response JSON:
```json
{
    "isGarden": true,
    "isAnalyzable": true,
    "climateCode": "TEMPERATE_CONTINENTAL",
    "description": {
        "summary": "Small sunny garden",
        "observations": ["Lawn", "Fence"]
    }
}
```
The backend rejects missing/incorrect required fields and unsupported climate codes. Climate cannot be established reliably from an image alone; the external adapter should combine image analysis with verified location/questionnaire data in a future iteration. Mediterranean, oceanic and alpine climates are European; this MVP deliberately supports only temperate continental gardens.

## Workflow
`RECEIVED/INITIALIZED` → `CHECKED/IN_PROGRESS` → `TRANSFERRED/IN_PROGRESS` → `ANALYZED/IN_PROGRESS` → `ACCEPTED/COMPLETED` or `REJECTED/COMPLETED`.
Provider failure: `TRANSFER_FAILED/FAILED`. Status history is retained in `garden_photo_status_history`.
Photo upload is `POST /api/v1/gardens/{gardenId}/photos` (multipart `file`). Status read: `GET /api/v1/gardens/{gardenId}/photos/{photoId}`.

## Operational cautions
A photo is persisted before the provider call, including when the provider is unavailable. The upload endpoint returns 502/503 on external errors, so the client must use a future photo-list endpoint or request identifier to recover the photo ID; currently the ID is not returned on error. Avoid logging image bytes or secrets. Obtain user consent for third-party photo transfer, define retention/deletion and access control before production. A database-backed image is acceptable for a small local MVP but object storage is preferred later.
