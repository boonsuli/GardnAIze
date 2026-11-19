-- Distinguish request lifecycle, per-module execution, and photo workflow.
ALTER TABLE public.garden_photo_requests
    ADD COLUMN attempt_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN lease_owner VARCHAR(120),
    ADD COLUMN lease_until TIMESTAMPTZ,
    ADD COLUMN finished_at TIMESTAMPTZ;
CREATE INDEX idx_photo_requests_claim ON public.garden_photo_requests(status, lease_until, created_at);

CREATE TABLE public.garden_photo_module_runs (
    id UUID PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES public.garden_photo_requests(request_id) ON DELETE CASCADE,
    module_name VARCHAR(24) NOT NULL CHECK (module_name IN ('VALID','SEGMENTATION','VISION','PLANT')),
    status VARCHAR(24) NOT NULL CHECK (status IN ('PENDING','RUNNING','COMPLETED','FAILED','SKIPPED','REJECTED')),
    attempt_number INTEGER NOT NULL DEFAULT 1,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    error_code VARCHAR(80),
    CONSTRAINT uq_photo_module_attempt UNIQUE(request_id,module_name,attempt_number)
);
CREATE INDEX idx_photo_module_request ON public.garden_photo_module_runs(request_id,module_name);

ALTER TABLE public.garden_photo_request_history
    ADD COLUMN module_name VARCHAR(24),
    ADD COLUMN previous_status VARCHAR(24),
    ADD COLUMN duration_ms BIGINT,
    ADD COLUMN error_code VARCHAR(80);
