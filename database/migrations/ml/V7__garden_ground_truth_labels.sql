-- Independent expert-reviewed supervised labels; never derived from K-Means.
CREATE TABLE horticulture.ml_garden_label (
 image_id bigint NOT NULL REFERENCES horticulture.garden_image_candidate(image_id) ON DELETE CASCADE,
 label_type text NOT NULL,
 label_value text NOT NULL,
 label_source text NOT NULL CHECK (label_source IN ('HUMAN','EXPERT')),
 reviewed_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(image_id,label_type),
 CHECK (length(trim(label_value))>0)
);
