# Master/Worker lifecycle and observability

## Three separate state machines

All values are stored as readable VARCHAR strings, never numeric ordinals.

**Request status** (`garden_photo_requests.status`):
- `ACCEPTED`: durable HTTP 202 acknowledgment, not yet claimed
- `RUNNING`: claimed by a worker
- `COMPLETED`: available pipeline completed (currently VALID + VISION)
- `FAILED`: technical error
- `REJECTED`: business rejection

**Photo workflow** (`garden_photos.workflow_status`):
`DRAFT`, `VALIDATING`, `VALID`, `NOT_VALID`, `VALIDATION_FAILED`,
`VISION_PENDING`, `VISION_PROCESSING`, `VISION_COMPLETED`, `VISION_FAILED`.
These states are constrained by the existing Flyway V12 migration. A future
migration should add `SEGMENTATION_*` and `PLANT_*` states when those modules
are integrated; do not insert undeclared values into the current CHECK constraint.

**Module run** (`garden_photo_module_runs.status`):
`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `SKIPPED`, `REJECTED`.
Module names: `VALID`, `SEGMENTATION`, `VISION`, `PLANT`.
Module run ID, request ID, module, attempt, timestamps and error code are persisted.

## Event vocabulary

- `REQUEST_RECORDED`
- `WORKER_CLAIMED`
- `VALID_STARTED`, `VALID_COMPLETED`, `VALID_FAILED`, `VALID_REJECTED`
- `VALIDATION_STARTED`, `VALIDATION_COMPLETED`, `VALIDATION_REJECTED`, `VALIDATION_FAILED`
- `VISION_STARTED`, `VISION_COMPLETED`, `VISION_FAILED`, `VISION_REJECTED`
- `WORKFLOW_COMPLETED`, `WORKFLOW_FAILED`, `WORKFLOW_REJECTED`
- `WORKER_DISPATCH_FAILED`, `WORKER_STATE_WRITE_FAILED`
- Future: `SEGMENTATION_STARTED/COMPLETED/FAILED/SKIPPED`,
  `PLANT_STARTED/COMPLETED/FAILED/SKIPPED`, `WORKER_RETRY`, `LEASE_EXPIRED`.

## Database lifecycle

- Flyway V14 creates persistent request and append-only request history.
- Flyway V15 adds lease owner/expiry, attempt counter, per-module runs,
  event module, previous state, duration and error-code columns.
- Master polls PostgreSQL every five seconds and claims a pending request
  with `FOR UPDATE SKIP LOCKED`; it never waits for Gemini to return.
- Worker validates the persisted image on the VALID pool, then invokes VISION
  on the VISION pool if VALID accepts it.
- Each module completion is recorded separately from request completion.

## Logging

Use SLF4J and Spring Boot's default Logback implementation.
Operational logs use `event`, `requestId`, `photoId`, `module`,
`status`, `attempt`, `errorCode`, and where available `durationMs`.
MDC carries `requestId` on worker threads; never log image bytes, image
base64, questionnaire answers, user descriptions, consent text or credentials.

Recommended additional signals: worker queue saturation, provider HTTP status
family, timeouts, duration, retry count, pending queue age, lease expiry,
consent decision, model version, response schema version, application startup
and shutdown, schema migration status, and failed database writes. These are
recommendations; not all are implemented in this increment.

## Important limitations before merge

- The worker currently supports VALID and VISION only. Segmentation and PLANT
  require their own contracts and implementations.
- The current worker persists VISION JSON, but does not yet recreate all
  existing normalized garden feature records from GardenPhotoService.
- An expired lease is not automatically replayed: replaying a non-idempotent
  external request could cause duplicate calls. Add lease renewal, safe
  idempotency and explicit recovery before claiming restart resilience.
- A worker may start before the accepting HTTP transaction commits; polling
  every five seconds usually avoids this but does not guarantee it.
- Request state transitions and photo/module transitions are separate
  transactions; strengthen invariants and reconcile partial failures.
- Tests and CI must be run and pass before merge. HTTP 202 means the request
  was accepted, not that processing succeeded.

## Update after PR #35 merge — 13 November 2026

The limitations and future-event notes above describe the **earlier implementation stage**. PR #35 subsequently added heartbeat renewal, `lease_generation` fencing, `RECONCILIATION_REQUIRED`, transactional `LEASE_EXPIRED` audit and PostgreSQL crash/rollback tests. **Do not use the earlier pre-merge limitations as the current implementation status.** The full current status catalog, transitions, event vocabulary and recovery boundaries are in [PHOTO_WORKFLOW_PR35.md](PHOTO_WORKFLOW_PR35.md). Expired VISION calls remain quarantined, not automatically replayed.
