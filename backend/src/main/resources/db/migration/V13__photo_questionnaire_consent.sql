CREATE TABLE IF NOT EXISTS public.garden_photo_questionnaire (
    photo_id UUID PRIMARY KEY REFERENCES public.garden_photos(id) ON DELETE CASCADE,
    answers JSONB NOT NULL,
    consent_key VARCHAR(120) NOT NULL,
    consented_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT chk_garden_photo_consent_key CHECK (consent_key = 'privacy.externalProcessingNotice'),
    CONSTRAINT chk_garden_photo_answers_object CHECK (jsonb_typeof(answers) = 'object')
);
