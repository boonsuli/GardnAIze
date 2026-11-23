# GDAI-BACK — VISION + PLANT orchestration (design, not yet implemented)

Branch: `feature/gdai-back-vision-plant-orchestration`. Baseline: PR #35 master/worker, leases, fencing and polling. This document defines the target behavior; it is **not evidence that the new flow is implemented or tested**.

## Consent gates

- After the user confirms the selected photo, BACK may perform local VALID preflight. **No image, description or personal data is sent to Gemini before explicit external-processing consent.**
- External-processing consent: mandatory to call Gemini. Decline => cancel the request; do not dispatch VISION or PLANT.
- GardnAIze model-training reuse consent: **separate and optional**. Decline => continue recommendations without retaining the image for training. Never make model-training consent a condition of service.
- Persist consent version, decision, timestamp and request linkage; distinguish withdrawal and retention policies. Recheck mandatory consent before external dispatch.
- FRONT communicates only with BACK.

## Proposed flow

1. FRONT uploads/previews photo (<=5 MiB) and user confirms.
2. BACK calls VALID via the existing preflight contract. Rejection stops the flow.
3. FRONT presents two distinct consents. BACK records mandatory external-processing consent and optional training consent; refusal of the mandatory consent cancels the external workflow.
4. After mandatory consent, BACK persists/claims a durable VISION task and dispatches VISION asynchronously; FRONT shows the standard questionnaire in parallel.
5. VISION result is persisted and BACK selects **at most one** context question, based on observed features and property coverage in the PLANT catalog; do not duplicate a question already answered.
6. FRONT polls or subscribes through BACK for context-question readiness. Preserve already-entered answers; deliver a stable question ID so late responses do not cause duplicates.
7. A join gate waits for required questionnaire answers, contextual-question resolution (answered, not applicable, or timeout fallback) and usable VISION output, then dispatches PLANT FastAPI.
8. Persist the five ranked recommendations, expose them via BACK and mark the overall request COMPLETED only after successful persistence.

## Minimal states

- Request: reuse `ACCEPTED`, `RUNNING`, `COMPLETED`, `FAILED`, `REJECTED`, `RECONCILIATION_REQUIRED` from PR #35. Do not invent a request status for every UI step.
- Modules: reuse `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `SKIPPED`, `REJECTED`; distinguish `VALID`, `VISION`, `PLANT` by module name.
- Questionnaire/context readiness is **separate metadata**, not a proliferation of request statuses: `WAITING`, `READY`, `RESOLVED` or a nullable question ID plus timestamps.
- Consent decisions are explicit values, not workflow statuses.

## Bounded waiting and failure policy

- Standard questionnaire must remain usable while VISION runs.
- If VISION finishes late, publish the contextual question only if the questionnaire is still open. Otherwise record a deterministic skip/fallback; do not overwrite answers.
- Use configurable deadlines for context-question selection and for user response. Expiration skips the **optional context question**, not mandatory consent or mandatory questionnaire fields.
- PLANT cannot run without the required VISION-derived input unless its **actual FastAPI contract** explicitly supports a validated fallback input. A VISION failure must be reported or handled by a tested degraded mode; never fabricate vision observations.
- If fewer than five plants meet hard horticultural constraints, return a transparent partial result rather than inventing plants.
- Respect PR #35 lease fencing and atomic state/history writes. Expired leases remain `RECONCILIATION_REQUIRED` without automatic replay of potentially billable Gemini calls.
- GDAI-AGENT, GDAI-SEGMT and GDAI-GNERAT are optional and must not block recommendations.

## Implementation checkpoints

1. Inspect the current GDAI-PLANT FastAPI route, request schema and response schema; define typed Java DTOs from real code.
2. Refactor the PR #35 acceptance/dispatch boundary so consent and VISION can precede final questionnaire submission; avoid duplicate VALID calls while ensuring persisted photo identity and integrity.
3. Add durable VISION and questionnaire join logic; context-question selection and bounded fallback.
4. Add PLANT client, worker dispatch, recommendation persistence and result API; extend Flyway as needed.
5. Extend Angular polling, question rendering and consent UI without direct calls to Python services.
6. Add unit/integration tests for mandatory-consent refusal, optional-training refusal, early/late VISION, context timeout, VISION failure, PLANT success/failure, lease expiry and stale writes.
7. Verify live FastAPI VALID/VISION/PLANT compatibility and Docker E2E; mocked integration tests alone are insufficient.

## Existing reference

See [PR #35 workflow](PHOTO_WORKFLOW_PR35.md). Its existing flow requires questionnaire and consent before queueing VALID/VISION. This branch must intentionally revise that ordering; do not claim the current implementation already supports parallel questionnaire and VISION.
