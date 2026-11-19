-- V10: auditable, multi-source temperate outdoor plant catalogue.
-- Candidate != validated: never infer hardiness or outdoor suitability from taxonomy.
CREATE TABLE horticulture.ml_plant_catalog (
 plant_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 scientific_name text NOT NULL,
 cultivar text NOT NULL DEFAULT '',
 canonical_key text NOT NULL UNIQUE,
 common_name_fr text,
 common_name_en text,
 growth_form text,
 outdoor_confirmed boolean,
 temperate_confirmed boolean,
 hardiness_min_c numeric(5,1),
 height_cm numeric(8,1),
 spread_cm numeric(8,1),
 exposure text,
 soil_texture text,
 soil_ph text,
 water_requirement text,
 maintenance text,
 evergreen boolean,
 flowering_months integer[],
 flower_color text,
 foliage_color text,
 drought_tolerance text,
 heat_tolerance text,
 pollinator_friendly boolean,
 allergenic_pollen boolean,
 privacy_screen boolean,
 attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
 quality_status text NOT NULL DEFAULT 'PENDING'
   CHECK (quality_status IN ('PENDING','REVIEW','VALIDATED','REJECTED')),
 ready_for_matching boolean NOT NULL DEFAULT false,
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 CHECK (height_cm IS NULL OR height_cm >= 0),
 CHECK (spread_cm IS NULL OR spread_cm >= 0),
 CHECK (flowering_months IS NULL OR flowering_months <@ ARRAY[1,2,3,4,5,6,7,8,9,10,11,12]),
 CHECK (NOT ready_for_matching OR
        (quality_status='VALIDATED' AND outdoor_confirmed IS TRUE AND temperate_confirmed IS TRUE))
);
CREATE INDEX idx_ml_plant_catalog_filter ON horticulture.ml_plant_catalog(quality_status,ready_for_matching);
CREATE INDEX idx_ml_plant_catalog_name ON horticulture.ml_plant_catalog(lower(scientific_name));
CREATE TABLE horticulture.ml_plant_source_record (
 source_key text NOT NULL,
 external_id text NOT NULL,
 plant_id bigint NOT NULL REFERENCES horticulture.ml_plant_catalog(plant_id),
 source_url text NOT NULL,
 source_version text,
 license_id text NOT NULL,
 commercial_reuse_allowed boolean NOT NULL DEFAULT false,
 retrieved_at timestamptz NOT NULL DEFAULT now(),
 payload jsonb NOT NULL,
 PRIMARY KEY(source_key,external_id)
);
CREATE INDEX idx_ml_plant_source_record_plant ON horticulture.ml_plant_source_record(plant_id);
CREATE TABLE horticulture.ml_plant_attribute_evidence (
 evidence_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 plant_id bigint NOT NULL REFERENCES horticulture.ml_plant_catalog(plant_id),
 source_key text NOT NULL,
 external_id text NOT NULL,
 attribute_name text NOT NULL,
 value_reported jsonb NOT NULL,
 reviewed boolean NOT NULL DEFAULT false,
 recorded_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(plant_id,source_key,external_id,attribute_name),
 FOREIGN KEY(source_key,external_id)
 REFERENCES horticulture.ml_plant_source_record(source_key,external_id)
);
CREATE TABLE horticulture.ml_plant_image (
 image_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 plant_id bigint NOT NULL REFERENCES horticulture.ml_plant_catalog(plant_id),
 source_key text NOT NULL,
 external_id text NOT NULL,
 original_url text NOT NULL,
 local_uri text,
 sha256 char(64),
 mime_type text,
 attribution text,
 license_id text NOT NULL,
 license_url text,
 representative boolean NOT NULL DEFAULT false,
 rights_reviewed boolean NOT NULL DEFAULT false,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(plant_id,original_url),
 CHECK (NOT representative OR rights_reviewed)
);
CREATE UNIQUE INDEX uq_ml_plant_representative ON horticulture.ml_plant_image(plant_id)
 WHERE representative;
COMMENT ON TABLE horticulture.ml_plant_catalog IS 'Candidate botanical catalogue; validation and matching eligibility require independent review.';
COMMENT ON TABLE horticulture.ml_plant_image IS 'Image metadata and optional local URI. Download/copy only after explicit media rights review.';
