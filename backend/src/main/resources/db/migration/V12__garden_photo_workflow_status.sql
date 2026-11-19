-- Keep one canonical current state on the photo, plus the existing audit history.
-- The previous photo_status and processing_status columns remain for legacy readers.
ALTER TABLE public.garden_photos
    ADD COLUMN workflow_status VARCHAR(40) NOT NULL DEFAULT 'DRAFT',
    ADD COLUMN validation_reason VARCHAR(300),
    ADD COLUMN validated_at TIMESTAMPTZ,
    ADD COLUMN vision_completed_at TIMESTAMPTZ;

ALTER TABLE public.garden_photos
    ADD CONSTRAINT chk_garden_photo_workflow_status CHECK (workflow_status IN (
        'DRAFT','VALIDATING','VALID','NOT_VALID','VALIDATION_FAILED',
        'VISION_PENDING','VISION_PROCESSING','VISION_COMPLETED','VISION_FAILED'
    ));

-- Preserve the semantic state of records uploaded before this migration.
UPDATE public.garden_photos SET workflow_status = CASE
    WHEN photo_status = 'REJECTED' THEN 'NOT_VALID'
    WHEN photo_status = 'ACCEPTED' OR photo_status = 'ANALYZED' THEN 'VISION_COMPLETED'
    WHEN photo_status = 'TRANSFER_FAILED' THEN 'VISION_FAILED'
    WHEN photo_status IN ('CHECKED','TRANSFERRED') THEN 'VISION_PROCESSING'
    ELSE 'DRAFT'
END;

ALTER TABLE public.garden_photo_status_history
    ADD COLUMN workflow_status VARCHAR(40);

-- Historical events retain their original status columns; new events populate workflow_status.
CREATE INDEX idx_garden_photos_workflow_status ON public.garden_photos(workflow_status);
COMMENT ON COLUMN public.garden_photos.workflow_status IS
    'Canonical workflow state; legacy photo_status/processing_status retained during migration';
