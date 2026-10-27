-- Controlled vocabulary; safe to rerun.
BEGIN;
INSERT INTO horticulture.plant_type (code, display_name) VALUES
('TREE','Tree'),('SHRUB','Shrub'),('PERENNIAL','Perennial'),('ANNUAL','Annual'),
('GRASS','Ornamental grass'),('CLIMBER','Climber'),('SUCCULENT','Succulent'),
('BULB','Bulb'),('GROUND_COVER','Ground cover'),('PALM','Palm')
ON CONFLICT (code) DO NOTHING;
INSERT INTO horticulture.soil_type (code, display_name) VALUES
('SANDY','Sandy'),('LOAMY','Loamy'),('CLAY','Clay'),('CHALKY','Chalky'),
('SILTY','Silty'),('PEATY','Peaty'),('ROCKY','Rocky')
ON CONFLICT (code) DO NOTHING;
INSERT INTO horticulture.sun_exposure (code, display_name) VALUES
('FULL_SUN','Full sun'),('PARTIAL_SHADE','Partial shade'),('FULL_SHADE','Full shade')
ON CONFLICT (code) DO NOTHING;
INSERT INTO horticulture.plant_use (code, display_name) VALUES
('PRIVACY_SCREEN','Privacy screening'),('HEDGE','Hedge'),('ORNAMENTAL','Ornamental'),
('POLLINATOR','Pollinator support'),('GROUND_COVER','Ground cover'),
('CONTAINER','Container planting'),('SHADE','Shade provision'),
('LOW_WATER','Low-water landscaping')
ON CONFLICT (code) DO NOTHING;
INSERT INTO horticulture.plant_color (code, display_name) VALUES
('WHITE','White'),('PINK','Pink'),('RED','Red'),('ORANGE','Orange'),
('YELLOW','Yellow'),('BLUE','Blue'),('PURPLE','Purple'),('GREEN','Green'),
('SILVER','Silver'),('BRONZE','Bronze'),('VARIEGATED','Variegated')
ON CONFLICT (code) DO NOTHING;
COMMIT;
