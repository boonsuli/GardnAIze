-- Audit token usage; costs are computed with a separately versioned tariff schedule.
CREATE TABLE horticulture.ml_gemini_usage (
 usage_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 image_id bigint REFERENCES horticulture.garden_image_candidate(image_id),
 model_name text NOT NULL,
 prompt_tokens bigint,
 output_tokens bigint,
 total_tokens bigint,
 image_sha256 char(64),
 request_status text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_ml_gemini_usage_date ON horticulture.ml_gemini_usage(created_at);
