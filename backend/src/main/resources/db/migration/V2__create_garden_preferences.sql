-- Additional MVP questionnaire attributes; keep the existing garden_projects table intact.
CREATE TABLE garden_preferences (
    garden_id UUID PRIMARY KEY REFERENCES garden_projects(id) ON DELETE CASCADE,
    water_availability VARCHAR(16) NOT NULL,
    maintenance_preference VARCHAR(16) NOT NULL,
    evergreen_preferred BOOLEAN NOT NULL,
    privacy_screening_required BOOLEAN NOT NULL,
    desired_height_cm INTEGER,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT chk_water_availability CHECK (water_availability IN ('LOW','MODERATE','HIGH')),
    CONSTRAINT chk_maintenance_preference CHECK (maintenance_preference IN ('LOW','MODERATE','HIGH')),
    CONSTRAINT chk_desired_height CHECK (desired_height_cm IS NULL OR desired_height_cm BETWEEN 20 AND 3000)
);
