-- Staged intake: external consent precedes asynchronous VISION;
-- the standard questionnaire may be submitted later.
ALTER TABLE public.garden_photo_questionnaire
    ADD COLUMN training_consent BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN answers_submitted_at TIMESTAMPTZ;

-- Legacy PR35 submissions already contain the final questionnaire.
UPDATE public.garden_photo_questionnaire
SET answers_submitted_at = consented_at
WHERE answers_submitted_at IS NULL;

ALTER TABLE public.garden_photo_requests
    ADD COLUMN intake_mode VARCHAR(24) NOT NULL DEFAULT 'LEGACY'
        CHECK (intake_mode IN ('LEGACY', 'STAGED'));
