-- Additive migration: preserve V1-V3 and existing horticulture records.
ALTER TABLE horticulture.plant
    ADD COLUMN IF NOT EXISTS cultivar text,
    ADD COLUMN IF NOT EXISTS is_outdoor boolean,
    ADD COLUMN IF NOT EXISTS european_climate_compatible boolean,
    ADD COLUMN IF NOT EXISTS pollen_allergy_level varchar(20),
    ADD COLUMN IF NOT EXISTS pollinator_notes text,
    ADD COLUMN IF NOT EXISTS ingestion_completeness numeric(5,4),
    ADD COLUMN IF NOT EXISTS ready_for_matching boolean NOT NULL DEFAULT false;

ALTER TABLE horticulture.plant
    ADD CONSTRAINT chk_plant_pollen_allergy_level
        CHECK (pollen_allergy_level IS NULL OR pollen_allergy_level IN ('LOW','MODERATE','HIGH','UNKNOWN')),
    ADD CONSTRAINT chk_plant_ingestion_completeness
        CHECK (ingestion_completeness IS NULL OR ingestion_completeness BETWEEN 0 AND 1);

CREATE TABLE horticulture.plant_pollinator (
    plant_id bigint NOT NULL REFERENCES horticulture.plant(plant_id) ON DELETE CASCADE,
    insect_type varchar(60) NOT NULL,
    evidence_source_record_id bigint REFERENCES horticulture.plant_source_record(plant_source_record_id),
    PRIMARY KEY (plant_id, insect_type)
);

CREATE TABLE horticulture.plant_ingestion_review (
    review_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    plant_id bigint REFERENCES horticulture.plant(plant_id) ON DELETE CASCADE,
    canonical_key text NOT NULL,
    issue_type varchar(30) NOT NULL CHECK (issue_type IN ('CONFLICT','MISSING','TAXONOMY','LICENCE')),
    details jsonb NOT NULL,
    resolved boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_plant_ready_for_matching
    ON horticulture.plant(ready_for_matching) WHERE ready_for_matching;
COMMENT ON COLUMN horticulture.plant.ready_for_matching IS
'Must be explicitly validated after horticultural review; ingestion never sets true.';
