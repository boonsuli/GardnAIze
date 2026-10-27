-- ML-only training records; user-facing gardens, images and predictions belong to backend.
CREATE TABLE horticulture.ml_garden_sample (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 sample_name text,
 source_kind varchar(20) NOT NULL DEFAULT 'SYNTHETIC' CHECK (source_kind IN ('SYNTHETIC','CURATED','ANONYMIZED')),
 climate_zone varchar(40),
 area_m2 numeric(10,2) CHECK (area_m2 > 0),
 soil_ph numeric(3,1) CHECK (soil_ph BETWEEN 0 AND 14),
 soil_drainage varchar(20) CHECK (soil_drainage IN ('POOR','MODERATE','GOOD')),
 water_availability varchar(20) CHECK (water_availability IN ('LOW','MODERATE','HIGH')),
 sun_hours_per_day numeric(4,1) CHECK (sun_hours_per_day BETWEEN 0 AND 24),
 minimum_winter_temperature_c numeric(5,1),
 maximum_summer_temperature_c numeric(5,1),
 evergreen_preferred boolean,
 low_maintenance_preferred boolean,
 privacy_screening_required boolean,
 created_at timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE horticulture.ml_garden_sample IS 'Synthetic, curated or anonymized training samples, never canonical user projects.';
CREATE TABLE horticulture.ml_garden_plant_assessment (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 ml_garden_sample_id bigint NOT NULL REFERENCES horticulture.ml_garden_sample(id) ON DELETE CASCADE,
 plant_id bigint NOT NULL REFERENCES horticulture.plant(plant_id) ON DELETE CASCADE,
 relevance_grade smallint NOT NULL CHECK (relevance_grade BETWEEN 0 AND 3),
 label_source varchar(25) NOT NULL CHECK (label_source IN ('EXPERT','USER_FEEDBACK','RULE_DERIVED')),
 assessor_reference text,
 assessment_notes text,
 assessed_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_ml_assessment_sample ON horticulture.ml_garden_plant_assessment(ml_garden_sample_id);
CREATE INDEX idx_ml_assessment_plant ON horticulture.ml_garden_plant_assessment(plant_id);
CREATE TABLE horticulture.ml_experiment (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 experiment_name text NOT NULL,
 task_type varchar(30) NOT NULL CHECK (task_type IN ('CLUSTERING','CLASSIFICATION','REGRESSION','RANKING')),
 algorithm_name text NOT NULL,
 dataset_version text NOT NULL,
 code_version text,
 target_attribute text,
 evaluation_method text,
 metrics jsonb NOT NULL DEFAULT '{}'::jsonb,
 artifact_uri text,
 created_at timestamptz NOT NULL DEFAULT now()
);
