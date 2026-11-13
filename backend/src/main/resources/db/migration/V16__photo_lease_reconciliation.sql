-- A lease generation prevents stale workers from committing after ownership changes.
ALTER TABLE public.garden_photo_requests
    ADD COLUMN lease_generation BIGINT NOT NULL DEFAULT 0;
ALTER TABLE public.garden_photo_requests
    DROP CONSTRAINT chk_photo_request_status;
ALTER TABLE public.garden_photo_requests
    ADD CONSTRAINT chk_photo_request_status
    CHECK (status IN ('ACCEPTED','RUNNING','COMPLETED','FAILED','REJECTED','RECONCILIATION_REQUIRED'));
