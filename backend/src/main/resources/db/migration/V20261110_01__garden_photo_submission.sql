-- Persist only photos accepted by GDAI-VALID. Never store rejected uploads.
CREATE TABLE IF NOT EXISTS public.garden_photo_submission (
    id UUID PRIMARY KEY,
    description VARCHAR(2000) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    image BYTEA NOT NULL,
    status VARCHAR(32) NOT NULL,
    vision_json TEXT,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_garden_photo_submission_status
    ON public.garden_photo_submission (status);
