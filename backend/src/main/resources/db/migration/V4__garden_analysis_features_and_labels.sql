-- Three independent data levels: provider observations, verified ML features, and independent labels.
-- Existing garden_photos and garden_projects remain authoritative.
CREATE TABLE garden_photo_analysis (
    id UUID PRIMARY KEY,
    photo_id UUID NOT NULL REFERENCES garden_photos(id) ON DELETE CASCADE,
    provider_name VARCHAR(80) NOT NULL,
    model_name VARCHAR(120) NOT NULL,
    schema_version VARCHAR(20) NOT NULL,
    analysis_status VARCHAR(20) NOT NULL CHECK (analysis_status IN ('SUCCEEDED','REJECTED','FAILED')),
    raw_response JSONB NOT NULL,
    analyzed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (photo_id, provider_name, model_name, analyzed_at)
);
CREATE INDEX idx_garden_photo_analysis_photo ON garden_photo_analysis(photo_id, analyzed_at DESC);

CREATE TABLE garden_features (
    id UUID PRIMARY KEY,
    garden_id UUID NOT NULL REFERENCES garden_projects(id) ON DELETE CASCADE,
    source_photo_analysis_id UUID REFERENCES garden_photo_analysis(id) ON DELETE SET NULL,
    schema_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    space_type VARCHAR(40),
    shade_level VARCHAR(24),
    privacy_exposure VARCHAR(24),
    plantable_areas_detected BOOLEAN,
    visible_surfaces JSONB NOT NULL DEFAULT '[]'::jsonb,
    visible_vegetation JSONB NOT NULL DEFAULT '[]'::jsonb,
    climate_code VARCHAR(40),
    climate_source VARCHAR(24) NOT NULL DEFAULT 'UNKNOWN'
        CHECK (climate_source IN ('UNKNOWN','USER_CONFIRMED','OFFICIAL_DATA')),
    soil_type VARCHAR(24),
    soil_source VARCHAR(24) NOT NULL DEFAULT 'UNKNOWN'
        CHECK (soil_source IN ('UNKNOWN','USER_CONFIRMED','MEASURED')),
    feature_provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
    validated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (climate_code IS NULL OR climate_source <> 'UNKNOWN'),
    CHECK (soil_type IS NULL OR soil_source <> 'UNKNOWN')
);
CREATE INDEX idx_garden_features_garden ON garden_features(garden_id, created_at DESC);

-- Provisional botanical key until the curated plant catalog is migrated to Flyway.
-- Never use generated Gemini suggestions as expert ground truth.
CREATE TABLE garden_plant_assessment (
    id UUID PRIMARY KEY,
    garden_id UUID NOT NULL REFERENCES garden_projects(id) ON DELETE CASCADE,
    plant_scientific_name TEXT NOT NULL,
    relevance_grade SMALLINT NOT NULL CHECK (relevance_grade BETWEEN 0 AND 3),
    label_source VARCHAR(24) NOT NULL
        CHECK (label_source IN ('EXPERT','USER_FEEDBACK','RULE_DERIVED')),
    assessor_reference VARCHAR(120) NOT NULL,
    assessment_notes TEXT,
    assessed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (garden_id, plant_scientific_name, label_source, assessor_reference)
);
CREATE INDEX idx_garden_plant_assessment_garden ON garden_plant_assessment(garden_id);
COMMENT ON TABLE garden_plant_assessment IS
'Garden-plant labels independent of Gemini; RULE_DERIVED is not expert ground truth.';
