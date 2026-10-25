CREATE TABLE garden_photos (
    id UUID PRIMARY KEY,
    garden_id UUID NOT NULL REFERENCES garden_projects(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(40) NOT NULL,
    file_size_bytes BIGINT NOT NULL CHECK (file_size_bytes BETWEEN 1 AND 10485760),
    width_px INTEGER NOT NULL CHECK (width_px > 0),
    height_px INTEGER NOT NULL CHECK (height_px > 0),
    image_bytes BYTEA NOT NULL,
    photo_status VARCHAR(32) NOT NULL,
    processing_status VARCHAR(32) NOT NULL,
    analysis_provider VARCHAR(120),
    analysis_json JSONB,
    rejection_reason VARCHAR(300),
    error_message VARCHAR(300),
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (photo_status IN ('RECEIVED','CHECKED','TRANSFERRED','ANALYZED','ACCEPTED','REJECTED','TRANSFER_FAILED')),
    CHECK (processing_status IN ('INITIALIZED','IN_PROGRESS','COMPLETED','FAILED'))
);
CREATE INDEX idx_garden_photos_garden ON garden_photos(garden_id, received_at DESC);

CREATE TABLE garden_photo_status_history (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    photo_id UUID NOT NULL REFERENCES garden_photos(id) ON DELETE CASCADE,
    photo_status VARCHAR(32) NOT NULL,
    processing_status VARCHAR(32) NOT NULL,
    details VARCHAR(300),
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_photo_history_photo ON garden_photo_status_history(photo_id, changed_at);
