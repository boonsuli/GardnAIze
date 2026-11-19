-- ML-only provenance and reproducible dataset snapshots.
-- Application photos and consent remain in gardnaize.app_schema; no cross-database FK.
CREATE TABLE horticulture.ml_dataset_version (
 dataset_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 dataset_key text NOT NULL,
 version_tag text NOT NULL,
 purpose text NOT NULL CHECK (purpose IN ('GARDEN','PLANT','GARDEN_PLANT')),
 status text NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT','FROZEN','RETIRED')),
 created_at timestamptz NOT NULL DEFAULT now(),
 frozen_at timestamptz,
 manifest_sha256 char(64),
 notes text,
 UNIQUE(dataset_key,version_tag),
 CHECK ((status <> 'FROZEN') OR (frozen_at IS NOT NULL AND manifest_sha256 IS NOT NULL))
);
CREATE TABLE horticulture.ml_dataset_item (
 dataset_id bigint NOT NULL REFERENCES horticulture.ml_dataset_version(dataset_id) ON DELETE RESTRICT,
 item_kind text NOT NULL CHECK (item_kind IN ('GARDEN_IMAGE','PLANT')),
 item_id bigint NOT NULL,
 split text NOT NULL CHECK (split IN ('TRAIN','VAL','TEST')),
 source_reference text NOT NULL,
 content_sha256 char(64) NOT NULL,
 PRIMARY KEY(dataset_id,item_kind,item_id)
);
CREATE INDEX idx_ml_dataset_item_split ON horticulture.ml_dataset_item(dataset_id,split);
-- Only curated/consented and quality-checked material should be included in snapshots.
CREATE TABLE horticulture.ml_garden_features (
 image_id bigint PRIMARY KEY REFERENCES horticulture.garden_image_candidate(image_id) ON DELETE CASCADE,
 feature_values jsonb NOT NULL,
 feature_source text NOT NULL CHECK (feature_source IN ('HUMAN','GEMINI_VISION','OTHER_MODEL')),
 feature_model_version text,
 reviewed boolean NOT NULL DEFAULT false,
 extracted_at timestamptz NOT NULL DEFAULT now(),
 CHECK (jsonb_typeof(feature_values)='object')
);
CREATE TABLE horticulture.ml_classification_result (
 result_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 dataset_id bigint NOT NULL REFERENCES horticulture.ml_dataset_version(dataset_id),
 item_kind text NOT NULL CHECK (item_kind IN ('GARDEN_IMAGE','PLANT')),
 item_id bigint NOT NULL,
 algorithm text NOT NULL CHECK (algorithm IN ('KMEANS','KNN')),
 model_version text NOT NULL,
 predicted_label text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(dataset_id,item_kind,item_id,algorithm,model_version)
);
COMMENT ON TABLE horticulture.ml_dataset_item IS 'Immutable snapshot membership after dataset is frozen; application-origin images require independently recorded consent and admission.';
