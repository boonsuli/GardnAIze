# GDAI photo workflow — target REST contract (not yet fully implemented)

## Sources (same path)
- Gallery/file chooser: `<input type=file accept=image/jpeg,image/png,image/webp>`
- Mobile camera: `<input type=file capture=environment accept=image/jpeg,image/png,image/webp>`
Both yield a browser File, checked at <= 5 MiB. Show a read-only preview and editable short description (<= 1000 characters); user can replace the file before confirming. No upload before confirmation.

## Upload
1. FRONT creates a garden via `POST /api/v1/gardens` (country, city, climate included).
2. FRONT uploads multipart `file` and `description` to `POST /api/v1/gardens/{gardenId}/photos`.
3. BACK validates MIME *and actual image bytes*, size, and description, persists bytes and metadata in `garden_photos` as DRAFT, and responds `202 Accepted` with photoId, workflowStatus and polling URL.
4. BACK asynchronously moves to VALIDATING and calls GDAI-VALID (ResNet-18). The validator returns valid/invalid plus a machine-readable reason. BACK owns status updates.
5. Invalid => NOT_VALID; FRONT polls `GET /api/v1/gardens/{gardenId}/photos/{photoId}`, shows reason and requests a replacement. Transport/provider error => VALIDATION_FAILED, eligible for retry; do not misclassify as NOT_VALID.
6. Valid => VALID, then VISION_PENDING; BACK asynchronously invokes GDAI-VISION, sets VISION_PROCESSING, persists Gemini structured JSON in `garden_photo_analysis`, then VISION_COMPLETED or VISION_FAILED.
7. FRONT polls until terminal or actionable state; never invokes VALID or VISION directly.

## Status model
Canonical `garden_photos.workflow_status`: DRAFT, VALIDATING, VALID, NOT_VALID, VALIDATION_FAILED, VISION_PENDING, VISION_PROCESSING, VISION_COMPLETED, VISION_FAILED.
`garden_photo_status_history` is an audit trail, not a separate state lookup table. The existing `photo_status` and `processing_status` remain temporarily for legacy readers. Implement transition rules with optimistic concurrency or guarded SQL updates and audit in the same transaction. Retries must be idempotent.

## Important implementation gaps
The current GardenPhotoService performs synchronous external *vision* analysis during upload, and uses legacy statuses; it is **not** yet the described VALID-first asynchronous workflow. The current FRONT preview/confirmation does not upload the File. The FRONT accepts WebP while backend ImageIO accepts JPEG/PNG only; implement WebP decoding or convert explicitly. Flyway V12 only prepares storage; it does not activate this workflow. Do not merge PR #35 on the basis of this document/migration alone.

## Acceptance tests
- File picker and camera converge on same upload; replacing photo never uploads previous selection.
- Oversize, unsupported/corrupt file, and overlong description rejected by FRONT and BACK.
- 202 response after DRAFT persisted; VALID rejects with NOT_VALID and reason; transient failure => VALIDATION_FAILED.
- VALID accepted => VISION_PENDING => VISION_PROCESSING => VISION_COMPLETED; Gemini JSON persisted.
- Polling and refresh show consistent state; status history records every transition.
- No duplicate vision invocation on retries; concurrent status transitions guarded.
