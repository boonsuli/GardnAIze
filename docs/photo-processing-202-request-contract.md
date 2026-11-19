# Photo processing request: HTTP 202 and audit contract

The REST documentation is in English. This change belongs to PR #35 because it changes the GDAI-FRONT/GDAI-BACK submission contract.

## Submit
`POST /api/v1/gardens/{gardenId}/photos` multipart: `file`, optional `description`, `answersJson`, `consentKey=privacy.externalProcessingNotice`.

The backend validates the explicit consent and required questionnaire fields, normalizes and persists the photo, records the consent and creates a request plus audit event in one database transaction. It returns **202 Accepted** with a `Location` header and JSON containing `requestId`, `photoId`, `gardenId`, `status=ACCEPTED`, `createdAt`, `statusUrl`.

## Poll
`GET /api/v1/gardens/{gardenId}/photo-requests/{requestId}` returns the current request state. The frontend shows the returned request number in French or English and polls every 3 seconds for up to 100 checks. Never expose internal errors, image bytes, questionnaire answers, API keys or consent content in logs.

## Audit and logs
- `garden_photo_requests`: current request state and timestamps.
- `garden_photo_request_history`: append-only events, starting with `REQUEST_RECORDED`.
- Structured SLF4J logs: `requestId`, `gardenId`, `photoId`, state. Do not log photo content, personal descriptions, answers, secrets or full external payloads.

## Scope and remaining integration

**Important:** This PR increment persists and acknowledges requests but **does not yet dispatch** a worker to advance them from `ACCEPTED`. Polling therefore reports `ACCEPTED` until a later orchestration implementation updates the row and writes history. HTTP 202 means durable acceptance, not completed analysis.

Implement asynchronous GDAI-VISION dispatch and its failure/retry handling in the backend orchestration work before declaring the workflow E2E complete. GDAI-PLANT should be integrated in a separate PR after its service contract is ready. GDAI-VALID segmentation belongs to its own module PR and will later be invoked from the BACK orchestration. Persisting photo before server-side validation is an existing gap to close before merging.

A robust background dispatcher must claim persisted requests atomically, record every state transition in the history table, and recover requests after a restart. A `CompletableFuture` alone is not a durable job queue.

## Update after PR #35 merge — 13 November 2026

The preceding statement that the worker is not dispatched was accurate only for the original PR increment and is now superseded. The merged PR includes the Master/Worker VALID → VISION pipeline, heartbeat, generation fencing and transactional reconciliation. See [PHOTO_WORKFLOW_PR35.md](PHOTO_WORKFLOW_PR35.md) for the implemented state transitions and error paths. HTTP 202 still means **accepted, not completed**.
