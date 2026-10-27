-- ML-only Flyway V1: botanical taxonomy, features and provenance.
-- Dedicated schema avoids collisions with existing Spring Boot public tables.
BEGIN;
CREATE SCHEMA IF NOT EXISTS horticulture;

CREATE TABLE horticulture.plant_family (
    plant_family_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    scientific_name text NOT NULL UNIQUE,
    common_name text
);
CREATE TABLE horticulture.plant_genus (
    plant_genus_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    plant_family_id bigint REFERENCES horticulture.plant_family(plant_family_id),
    scientific_name text NOT NULL UNIQUE
);
CREATE TABLE horticulture.plant_type (
    plant_type_id smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code varchar(40) NOT NULL UNIQUE,
    display_name text NOT NULL
);
CREATE TABLE horticulture.soil_type (
    soil_type_id smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code varchar(40) NOT NULL UNIQUE,
    display_name text NOT NULL
);
CREATE TABLE horticulture.sun_exposure (
    sun_exposure_id smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code varchar(40) NOT NULL UNIQUE,
    display_name text NOT NULL
);
CREATE TABLE horticulture.plant_use (
    plant_use_id smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code varchar(50) NOT NULL UNIQUE,
    display_name text NOT NULL
);
CREATE TABLE horticulture.plant_color (
    plant_color_id smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code varchar(40) NOT NULL UNIQUE,
    display_name text NOT NULL
);

CREATE TABLE horticulture.data_source (
    data_source_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_name text NOT NULL UNIQUE,
    base_url text,
    license_name text,
    license_url text,
    terms_url text,
    commercial_reuse_allowed boolean,
    redistribution_allowed boolean,
    last_reviewed_at timestamptz
);
CREATE TABLE horticulture.import_run (
    import_run_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    data_source_id bigint NOT NULL REFERENCES horticulture.data_source(data_source_id),
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    status varchar(20) NOT NULL DEFAULT 'RUNNING'
        CHECK (status IN ('RUNNING','SUCCEEDED','PARTIAL','FAILED')),
    fetched_count integer NOT NULL DEFAULT 0 CHECK (fetched_count >= 0),
    accepted_count integer NOT NULL DEFAULT 0 CHECK (accepted_count >= 0),
    rejected_count integer NOT NULL DEFAULT 0 CHECK (rejected_count >= 0),
    error_message text
);

CREATE TABLE horticulture.plant (
    plant_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    scientific_name text NOT NULL,
    normalized_scientific_name text NOT NULL UNIQUE,
    common_name text,
    plant_genus_id bigint REFERENCES horticulture.plant_genus(plant_genus_id),
    plant_type_id smallint REFERENCES horticulture.plant_type(plant_type_id),
    is_evergreen boolean,
    is_perennial boolean,
    is_native boolean,
    is_invasive boolean,
    is_toxic_to_pets boolean,
    is_drought_tolerant boolean,
    is_heat_tolerant boolean,
    minimum_hardiness_c numeric(5,1),
    maximum_temperature_c numeric(5,1),
    minimum_height_cm integer CHECK (minimum_height_cm >= 0),
    maximum_height_cm integer CHECK (maximum_height_cm >= minimum_height_cm),
    minimum_spread_cm integer CHECK (minimum_spread_cm >= 0),
    maximum_spread_cm integer CHECK (maximum_spread_cm >= minimum_spread_cm),
    minimum_soil_ph numeric(3,1) CHECK (minimum_soil_ph BETWEEN 0 AND 14),
    maximum_soil_ph numeric(3,1) CHECK (maximum_soil_ph BETWEEN 0 AND 14 AND maximum_soil_ph >= minimum_soil_ph),
    water_requirement varchar(20) CHECK (water_requirement IN ('LOW','MODERATE','HIGH')),
    fertilizer_requirement varchar(20) CHECK (fertilizer_requirement IN ('NONE','LOW','MODERATE','HIGH')),
    pruning_requirement varchar(20) CHECK (pruning_requirement IN ('NONE','LOW','MODERATE','HIGH')),
    maintenance_level varchar(20) CHECK (maintenance_level IN ('LOW','MODERATE','HIGH')),
    growth_rate varchar(20) CHECK (growth_rate IN ('SLOW','MODERATE','FAST')),
    minimum_spacing_cm integer CHECK (minimum_spacing_cm >= 0),
    description text,
    quality_status varchar(20) NOT NULL DEFAULT 'PENDING'
        CHECK (quality_status IN ('PENDING','VALIDATED','REJECTED')),
    validation_notes text,
    validated_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
COMMENT ON COLUMN horticulture.plant.normalized_scientific_name IS
'Canonical taxon key; review synonyms/cultivars before merging. No automatic species equivalence.';
COMMENT ON COLUMN horticulture.plant.minimum_hardiness_c IS
'Lowest tolerated temperature in degrees Celsius, not a USDA zone.';
COMMENT ON COLUMN horticulture.plant.water_requirement IS
'Observed/verified categorical care need; model predictions are stored separately.';

CREATE TABLE horticulture.plant_source_record (
    plant_source_record_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    plant_id bigint REFERENCES horticulture.plant(plant_id) ON DELETE SET NULL,
    data_source_id bigint NOT NULL REFERENCES horticulture.data_source(data_source_id),
    import_run_id bigint REFERENCES horticulture.import_run(import_run_id),
    external_plant_id text NOT NULL,
    scientific_name_as_reported text,
    source_url text,
    retrieved_at timestamptz NOT NULL DEFAULT now(),
    raw_payload jsonb NOT NULL,
    normalization_warnings jsonb NOT NULL DEFAULT '[]'::jsonb,
    UNIQUE (data_source_id, external_plant_id)
);
CREATE INDEX idx_plant_source_record_plant ON horticulture.plant_source_record(plant_id);
CREATE INDEX idx_plant_source_record_import ON horticulture.plant_source_record(import_run_id);

CREATE TABLE horticulture.plant_soil_type (
    plant_id bigint NOT NULL REFERENCES horticulture.plant(plant_id) ON DELETE CASCADE,
    soil_type_id smallint NOT NULL REFERENCES horticulture.soil_type(soil_type_id),
    suitability varchar(20) NOT NULL DEFAULT 'SUITABLE'
        CHECK (suitability IN ('PREFERRED','SUITABLE','UNSUITABLE')),
    PRIMARY KEY (plant_id, soil_type_id)
);
CREATE TABLE horticulture.plant_sun_exposure (
    plant_id bigint NOT NULL REFERENCES horticulture.plant(plant_id) ON DELETE CASCADE,
    sun_exposure_id smallint NOT NULL REFERENCES horticulture.sun_exposure(sun_exposure_id),
    suitability varchar(20) NOT NULL DEFAULT 'SUITABLE'
        CHECK (suitability IN ('PREFERRED','SUITABLE','UNSUITABLE')),
    PRIMARY KEY (plant_id, sun_exposure_id)
);
CREATE TABLE horticulture.plant_use_assignment (
    plant_id bigint NOT NULL REFERENCES horticulture.plant(plant_id) ON DELETE CASCADE,
    plant_use_id smallint NOT NULL REFERENCES horticulture.plant_use(plant_use_id),
    PRIMARY KEY (plant_id, plant_use_id)
);
CREATE TABLE horticulture.plant_color_assignment (
    plant_id bigint NOT NULL REFERENCES horticulture.plant(plant_id) ON DELETE CASCADE,
    plant_color_id smallint NOT NULL REFERENCES horticulture.plant_color(plant_color_id),
    color_context varchar(20) NOT NULL CHECK (color_context IN ('FLOWER','FOLIAGE','BARK','FRUIT')),
    PRIMARY KEY (plant_id, plant_color_id, color_context)
);
CREATE TABLE horticulture.plant_flowering_period (
    plant_id bigint NOT NULL REFERENCES horticulture.plant(plant_id) ON DELETE CASCADE,
    month_number smallint NOT NULL CHECK (month_number BETWEEN 1 AND 12),
    PRIMARY KEY (plant_id, month_number)
);
CREATE TABLE horticulture.plant_attribute_evidence (
    plant_attribute_evidence_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    plant_id bigint NOT NULL REFERENCES horticulture.plant(plant_id) ON DELETE CASCADE,
    attribute_name varchar(80) NOT NULL,
    data_source_id bigint REFERENCES horticulture.data_source(data_source_id),
    source_record_id bigint REFERENCES horticulture.plant_source_record(plant_source_record_id),
    value_as_reported jsonb NOT NULL,
    evidence_type varchar(20) NOT NULL CHECK (evidence_type IN ('OBSERVED','EXPERT_REVIEWED','MODEL_PREDICTED')),
    model_version text,
    confidence_score numeric(5,4) CHECK (confidence_score BETWEEN 0 AND 1),
    recorded_at timestamptz NOT NULL DEFAULT now(),
    CHECK (evidence_type <> 'MODEL_PREDICTED' OR model_version IS NOT NULL)
);
CREATE INDEX idx_plant_evidence_attribute ON horticulture.plant_attribute_evidence(plant_id, attribute_name, evidence_type);
CREATE INDEX idx_plant_quality ON horticulture.plant(quality_status);
CREATE INDEX idx_plant_type ON horticulture.plant(plant_type_id);
COMMIT;
