-- GardnAIze PostgreSQL 18 domain schema (Flyway, forward-only)
-- Naming: plant_ botanical, garden_ garden, ml_ machine learning,
-- assoc_ relationships, ingest_ provenance/import, ref_ shared reference.
-- All timestamps are UTC-aware; application supplies business UUIDs.
CREATE SCHEMA IF NOT EXISTS gardnaize;

CREATE TABLE gardnaize.ref_data_source (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_name VARCHAR(160) NOT NULL,
    source_url TEXT,
    license_name VARCHAR(160),
    license_url TEXT,
    attribution TEXT,
    commercial_use_reviewed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_ref_data_source_name UNIQUE (source_name)
);

CREATE TABLE gardnaize.ingest_batch (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    data_source_id BIGINT NOT NULL REFERENCES gardnaize.ref_data_source(id) ON DELETE RESTRICT,
    dataset_kind VARCHAR(20) NOT NULL CHECK (dataset_kind IN ('PLANT','GARDEN')),
    source_version VARCHAR(120),
    source_checksum_sha256 CHAR(64),
    status VARCHAR(20) NOT NULL DEFAULT 'STARTED'
        CHECK (status IN ('STARTED','VALIDATED','COMPLETED','FAILED')),
    total_rows INTEGER CHECK (total_rows IS NULL OR total_rows >= 0),
    accepted_rows INTEGER CHECK (accepted_rows IS NULL OR accepted_rows >= 0),
    rejected_rows INTEGER CHECK (rejected_rows IS NULL OR rejected_rows >= 0),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    error_summary TEXT,
    CONSTRAINT ck_ingest_finished_after_started CHECK (finished_at IS NULL OR finished_at >= started_at)
);
CREATE INDEX idx_ingest_batch_source ON gardnaize.ingest_batch(data_source_id, started_at DESC);

CREATE TABLE gardnaize.plant_species (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    scientific_name VARCHAR(255) NOT NULL,
    common_name VARCHAR(255),
    family_name VARCHAR(160),
    genus VARCHAR(160),
    evergreen BOOLEAN,
    min_hardiness_c NUMERIC(5,2),
    mature_height_cm INTEGER CHECK (mature_height_cm IS NULL OR mature_height_cm > 0),
    mature_spread_cm INTEGER CHECK (mature_spread_cm IS NULL OR mature_spread_cm > 0),
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_plant_species_scientific_name UNIQUE (scientific_name)
);

CREATE TABLE gardnaize.plant_care_profile (
    plant_id BIGINT PRIMARY KEY REFERENCES gardnaize.plant_species(id) ON DELETE CASCADE,
    sunlight VARCHAR(20) CHECK (sunlight IN ('FULL_SUN','PART_SHADE','SHADE','VARIABLE')),
    soil_drainage VARCHAR(20) CHECK (soil_drainage IN ('FAST','MODERATE','SLOW','VARIABLE')),
    water_need VARCHAR(20) CHECK (water_need IN ('LOW','MEDIUM','HIGH')),
    maintenance_level VARCHAR(20) CHECK (maintenance_level IN ('LOW','MEDIUM','HIGH')),
    drought_tolerant BOOLEAN,
    notes TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE gardnaize.garden_project (
    id UUID PRIMARY KEY,
    title VARCHAR(180),
    climate_region VARCHAR(120),
    sunlight VARCHAR(20) CHECK (sunlight IN ('FULL_SUN','PART_SHADE','SHADE','VARIABLE')),
    soil_drainage VARCHAR(20) CHECK (soil_drainage IN ('FAST','MODERATE','SLOW','UNKNOWN')),
    water_availability VARCHAR(20) CHECK (water_availability IN ('LOW','MEDIUM','HIGH','UNKNOWN')),
    maintenance_preference VARCHAR(20) CHECK (maintenance_preference IN ('LOW','MEDIUM','HIGH','UNKNOWN')),
    min_winter_temp_c NUMERIC(5,2),
    available_area_m2 NUMERIC(10,2) CHECK (available_area_m2 IS NULL OR available_area_m2 > 0),
    preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE gardnaize.garden_image (
    id UUID PRIMARY KEY,
    garden_id UUID NOT NULL REFERENCES gardnaize.garden_project(id) ON DELETE CASCADE,
    object_key TEXT NOT NULL,
    content_type VARCHAR(80) NOT NULL CHECK (content_type IN ('image/jpeg','image/png','image/webp')),
    width_px INTEGER CHECK (width_px IS NULL OR width_px > 0),
    height_px INTEGER CHECK (height_px IS NULL OR height_px > 0),
    validation_status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (validation_status IN ('PENDING','ACCEPTED','REJECTED')),
    vision_provider VARCHAR(80),
    vision_observations JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_garden_image_object_key UNIQUE (object_key)
);
CREATE INDEX idx_garden_image_garden ON gardnaize.garden_image(garden_id);

CREATE TABLE gardnaize.ml_model_version (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_name VARCHAR(160) NOT NULL,
    algorithm VARCHAR(60) NOT NULL,
    model_version VARCHAR(80) NOT NULL,
    artifact_uri TEXT,
    training_dataset_checksum CHAR(64),
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    trained_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_ml_model_version UNIQUE (model_name, model_version)
);

CREATE TABLE gardnaize.ml_experiment (
    id UUID PRIMARY KEY,
    model_version_id BIGINT REFERENCES gardnaize.ml_model_version(id) ON DELETE SET NULL,
    ingest_batch_id BIGINT REFERENCES gardnaize.ingest_batch(id) ON DELETE SET NULL,
    experiment_name VARCHAR(180) NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE gardnaize.ml_recommendation (
    id UUID PRIMARY KEY,
    garden_id UUID NOT NULL REFERENCES gardnaize.garden_project(id) ON DELETE CASCADE,
    model_version_id BIGINT REFERENCES gardnaize.ml_model_version(id) ON DELETE SET NULL,
    strategy VARCHAR(60) NOT NULL DEFAULT 'RULES_AND_SIMILARITY',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_ml_recommendation_garden ON gardnaize.ml_recommendation(garden_id, created_at DESC);

CREATE TABLE gardnaize.assoc_plant_source (
    plant_id BIGINT NOT NULL REFERENCES gardnaize.plant_species(id) ON DELETE CASCADE,
    data_source_id BIGINT NOT NULL REFERENCES gardnaize.ref_data_source(id) ON DELETE RESTRICT,
    source_record_id VARCHAR(255) NOT NULL,
    ingest_batch_id BIGINT REFERENCES gardnaize.ingest_batch(id) ON DELETE SET NULL,
    source_attributes JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (plant_id, data_source_id, source_record_id)
);
CREATE INDEX idx_assoc_plant_source_source ON gardnaize.assoc_plant_source(data_source_id, source_record_id);

CREATE TABLE gardnaize.assoc_recommendation_plant (
    recommendation_id UUID NOT NULL REFERENCES gardnaize.ml_recommendation(id) ON DELETE CASCADE,
    plant_id BIGINT NOT NULL REFERENCES gardnaize.plant_species(id) ON DELETE RESTRICT,
    rank_position SMALLINT NOT NULL CHECK (rank_position > 0),
    score NUMERIC(8,6) CHECK (score IS NULL OR (score >= 0 AND score <= 1)),
    explanation TEXT,
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    PRIMARY KEY (recommendation_id, plant_id),
    CONSTRAINT uq_assoc_recommendation_rank UNIQUE (recommendation_id, rank_position)
);
CREATE INDEX idx_assoc_recommendation_plant ON gardnaize.assoc_recommendation_plant(plant_id);

COMMENT ON SCHEMA gardnaize IS 'GardnAIze MVP domain data; managed by Flyway';
COMMENT ON TABLE gardnaize.assoc_plant_source IS 'Plant-to-source lineage, including original source record ID';
COMMENT ON TABLE gardnaize.assoc_recommendation_plant IS 'Ranked many-to-many recommendation results';
