-- GardnAIze | Garden profiles, questionnaire, ML relevance and recommendations.
BEGIN;
CREATE TABLE horticulture.garden (
    garden_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_project_id uuid UNIQUE,
    garden_name text,
    country_code char(2) NOT NULL DEFAULT 'FR',
    region_code varchar(30),
    department_code varchar(10),
    climate_zone varchar(40),
    latitude numeric(9,6) CHECK (latitude BETWEEN -90 AND 90),
    longitude numeric(9,6) CHECK (longitude BETWEEN -180 AND 180),
    area_m2 numeric(10,2) CHECK (area_m2 > 0),
    soil_ph numeric(3,1) CHECK (soil_ph BETWEEN 0 AND 14),
    soil_drainage varchar(20) CHECK (soil_drainage IN ('POOR','MODERATE','GOOD')),
    water_availability varchar(20) CHECK (water_availability IN ('LOW','MODERATE','HIGH')),
    irrigation_available boolean,
    sun_hours_per_day numeric(4,1) CHECK (sun_hours_per_day BETWEEN 0 AND 24),
    minimum_winter_temperature_c numeric(5,1),
    maximum_summer_temperature_c numeric(5,1),
    desired_minimum_height_cm integer CHECK (desired_minimum_height_cm >= 0),
    desired_maximum_height_cm integer CHECK (desired_maximum_height_cm >= desired_minimum_height_cm),
    evergreen_preferred boolean,
    low_maintenance_preferred boolean,
    privacy_screening_required boolean,
    notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE horticulture.garden IS 'Garden site and user preferences, independent of plant taxonomy.';
COMMENT ON COLUMN horticulture.garden.latitude IS 'Optional sensitive location; avoid exporting into public ML datasets.';

CREATE TABLE horticulture.garden_soil_type (
    garden_id bigint NOT NULL REFERENCES horticulture.garden(garden_id) ON DELETE CASCADE,
    soil_type_id smallint NOT NULL REFERENCES horticulture.soil_type(soil_type_id),
    PRIMARY KEY (garden_id, soil_type_id)
);
CREATE TABLE horticulture.garden_sun_exposure (
    garden_id bigint NOT NULL REFERENCES horticulture.garden(garden_id) ON DELETE CASCADE,
    sun_exposure_id smallint NOT NULL REFERENCES horticulture.sun_exposure(sun_exposure_id),
    PRIMARY KEY (garden_id, sun_exposure_id)
);
CREATE TABLE horticulture.garden_plant_use_preference (
    garden_id bigint NOT NULL REFERENCES horticulture.garden(garden_id) ON DELETE CASCADE,
    plant_use_id smallint NOT NULL REFERENCES horticulture.plant_use(plant_use_id),
    priority smallint NOT NULL DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
    PRIMARY KEY (garden_id, plant_use_id)
);
CREATE TABLE horticulture.garden_photo (
    garden_photo_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    garden_id bigint NOT NULL REFERENCES horticulture.garden(garden_id) ON DELETE CASCADE,
    storage_key text NOT NULL,
    media_type varchar(40) NOT NULL CHECK (media_type IN ('image/jpeg','image/png','image/webp')),
    size_bytes bigint NOT NULL CHECK (size_bytes > 0),
    width_px integer CHECK (width_px > 0),
    height_px integer CHECK (height_px > 0),
    uploaded_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz
);
CREATE TABLE horticulture.garden_photo_analysis (
    garden_photo_analysis_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    garden_photo_id bigint NOT NULL REFERENCES horticulture.garden_photo(garden_photo_id) ON DELETE CASCADE,
    model_provider text NOT NULL,
    model_name text NOT NULL,
    model_version text,
    is_garden boolean,
    is_landscapable boolean,
    analysis_status varchar(20) NOT NULL CHECK (analysis_status IN ('PENDING','SUCCEEDED','REJECTED','FAILED')),
    structured_observations jsonb NOT NULL DEFAULT '{}'::jsonb,
    user_confirmed_at timestamptz,
    analyzed_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE horticulture.garden_questionnaire_response (
    garden_questionnaire_response_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    garden_id bigint NOT NULL REFERENCES horticulture.garden(garden_id) ON DELETE CASCADE,
    question_code varchar(80) NOT NULL,
    answer_value jsonb NOT NULL,
    answered_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (garden_id, question_code)
);

-- Training/evaluation evidence: labels are distinct from generated recommendations.
CREATE TABLE horticulture.garden_plant_assessment (
    garden_plant_assessment_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    garden_id bigint NOT NULL REFERENCES horticulture.garden(garden_id) ON DELETE CASCADE,
    plant_id bigint NOT NULL REFERENCES horticulture.plant(plant_id) ON DELETE CASCADE,
    relevance_grade smallint NOT NULL CHECK (relevance_grade BETWEEN 0 AND 3),
    label_source varchar(25) NOT NULL CHECK (label_source IN ('EXPERT','USER_FEEDBACK','RULE_DERIVED')),
    assessor_reference text,
    assessment_notes text,
    assessed_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (garden_id, plant_id, label_source, assessor_reference)
);
COMMENT ON TABLE horticulture.garden_plant_assessment IS
'Independent relevance labels for ranking/classification. RULE_DERIVED labels must not be presented as expert ground truth.';
CREATE INDEX idx_garden_plant_assessment_garden ON horticulture.garden_plant_assessment(garden_id);
CREATE INDEX idx_garden_plant_assessment_plant ON horticulture.garden_plant_assessment(plant_id);

CREATE TABLE horticulture.ml_experiment (
    ml_experiment_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
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
CREATE TABLE horticulture.recommendation_run (
    recommendation_run_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    garden_id bigint NOT NULL REFERENCES horticulture.garden(garden_id) ON DELETE CASCADE,
    ml_experiment_id bigint REFERENCES horticulture.ml_experiment(ml_experiment_id),
    model_version text,
    filtering_rules_version text,
    generated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE horticulture.garden_plant_recommendation (
    recommendation_run_id bigint NOT NULL REFERENCES horticulture.recommendation_run(recommendation_run_id) ON DELETE CASCADE,
    plant_id bigint NOT NULL REFERENCES horticulture.plant(plant_id),
    rank_position smallint NOT NULL CHECK (rank_position > 0),
    relevance_score numeric(8,6),
    justification text,
    warnings jsonb NOT NULL DEFAULT '[]'::jsonb,
    PRIMARY KEY (recommendation_run_id, plant_id),
    UNIQUE (recommendation_run_id, rank_position)
);
CREATE INDEX idx_garden_country_region ON horticulture.garden(country_code, region_code);
CREATE INDEX idx_garden_photo_garden ON horticulture.garden_photo(garden_id);
CREATE INDEX idx_recommendation_garden ON horticulture.recommendation_run(garden_id);
COMMIT;
