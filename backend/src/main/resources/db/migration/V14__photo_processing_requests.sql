-- Persistent request identity and append-only audit trail.
CREATE TABLE public.garden_photo_requests (
    request_id UUID PRIMARY KEY,
    garden_id UUID NOT NULL REFERENCES public.garden_projects(id) ON DELETE CASCADE,
    photo_id UUID NOT NULL UNIQUE REFERENCES public.garden_photos(id) ON DELETE CASCADE,
    status VARCHAR(24) NOT NULL DEFAULT 'ACCEPTED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_photo_request_status CHECK (status IN ('ACCEPTED','RUNNING','COMPLETED','FAILED','REJECTED'))
);
CREATE INDEX idx_garden_photo_requests_garden ON public.garden_photo_requests(garden_id, created_at DESC);

CREATE TABLE public.garden_photo_request_history (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES public.garden_photo_requests(request_id) ON DELETE CASCADE,
    status VARCHAR(24) NOT NULL,
    event_code VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_garden_photo_request_history_request ON public.garden_photo_request_history(request_id, created_at);
