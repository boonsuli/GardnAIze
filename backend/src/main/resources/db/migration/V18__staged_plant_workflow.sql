-- Separate completed VISION from completed recommendations for staged requests.
ALTER TABLE public.garden_photo_requests DROP CONSTRAINT chk_photo_request_status;
ALTER TABLE public.garden_photo_requests ADD CONSTRAINT chk_photo_request_status
 CHECK (status IN ('ACCEPTED','RUNNING','WAITING_ANSWERS','READY_FOR_PLANT',
                   'COMPLETED','FAILED','REJECTED','RECONCILIATION_REQUIRED'));

ALTER TABLE public.garden_photos DROP CONSTRAINT chk_garden_photo_workflow_status;
ALTER TABLE public.garden_photos ADD CONSTRAINT chk_garden_photo_workflow_status
 CHECK (workflow_status IN (
 'DRAFT','VALIDATING','VALID','NOT_VALID','VALIDATION_FAILED',
 'VISION_PENDING','VISION_PROCESSING','VISION_COMPLETED','VISION_FAILED',
 'PLANT_PROCESSING','COMPLETED'
 ));

CREATE TABLE public.garden_photo_recommendations (
 request_id UUID PRIMARY KEY REFERENCES public.garden_photo_requests(request_id) ON DELETE CASCADE,
 recommendations JSONB NOT NULL,
 method VARCHAR(32),
 model_version VARCHAR(120),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 CONSTRAINT chk_recommendations_array CHECK (jsonb_typeof(recommendations) = 'array'),
 CONSTRAINT chk_recommendations_limit CHECK (jsonb_array_length(recommendations) BETWEEN 1 AND 10)
);
