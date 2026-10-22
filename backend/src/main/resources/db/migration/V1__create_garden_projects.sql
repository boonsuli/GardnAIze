CREATE TABLE garden_projects (
    id UUID PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    location VARCHAR(160) NOT NULL,
    exposure VARCHAR(24) NOT NULL,
    soil_type VARCHAR(24) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX idx_garden_projects_created_at ON garden_projects (created_at DESC);
