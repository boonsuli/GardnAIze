-- Expert-reviewed, independent labels for supervised plant classification.
CREATE TABLE horticulture.ml_plant_label (
 plant_id bigint NOT NULL REFERENCES horticulture.ml_plant_catalog(plant_id) ON DELETE CASCADE,
 label_type text NOT NULL,
 label_value text NOT NULL,
 label_source text NOT NULL DEFAULT 'HUMAN',
 reviewed boolean NOT NULL DEFAULT false,
 reviewed_at timestamptz,
 notes text,
 PRIMARY KEY(plant_id,label_type),
 CHECK (label_type IN ('PLANT_GARDEN_ROLE')),
 CHECK (label_source IN ('HUMAN','EXPERT','REFERENCE')),
 CHECK (NOT reviewed OR reviewed_at IS NOT NULL)
);
CREATE INDEX idx_ml_plant_label_type_value ON horticulture.ml_plant_label(label_type,label_value);
COMMENT ON TABLE horticulture.ml_plant_label IS 'Expert-confirmed ground truth for KNN; not inferred from K-Means clusters.';
