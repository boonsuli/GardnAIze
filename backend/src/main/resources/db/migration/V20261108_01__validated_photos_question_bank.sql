CREATE TABLE IF NOT EXISTS gdai_validated_photos (
    id UUID PRIMARY KEY,
    original_filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(64) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    image_data BYTEA NOT NULL,
    image_size_bytes INTEGER NOT NULL CHECK (image_size_bytes BETWEEN 1 AND 1048576),
    validation_model VARCHAR(80) NOT NULL DEFAULT 'resnet-18',
    validation_status VARCHAR(16) NOT NULL DEFAULT 'VALID' CHECK (validation_status = 'VALID'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS gdai_questions (
    id VARCHAR(80) PRIMARY KEY,
    answer_type VARCHAR(16) NOT NULL CHECK (answer_type IN ('text','select','number','boolean')),
    required BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INTEGER NOT NULL,
    feature_key VARCHAR(80) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TABLE IF NOT EXISTS gdai_question_translations (
    question_id VARCHAR(80) NOT NULL REFERENCES gdai_questions(id) ON DELETE CASCADE,
    language_code VARCHAR(10) NOT NULL,
    label TEXT NOT NULL,
    PRIMARY KEY (question_id, language_code)
);
CREATE TABLE IF NOT EXISTS gdai_question_rules (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    question_id VARCHAR(80) NOT NULL REFERENCES gdai_questions(id) ON DELETE CASCADE,
    continent_code VARCHAR(2),
    climate_code VARCHAR(40),
    country_code VARCHAR(2),
    CHECK (continent_code IS NULL OR continent_code IN ('EU','AF','AS','NA','SA','OC','AN'))
);
CREATE INDEX IF NOT EXISTS idx_gdai_question_rules ON gdai_question_rules(question_id, continent_code, climate_code, country_code);
CREATE TABLE IF NOT EXISTS gdai_question_options (
    question_id VARCHAR(80) NOT NULL REFERENCES gdai_questions(id) ON DELETE CASCADE,
    value VARCHAR(80) NOT NULL,
    display_order INTEGER NOT NULL,
    PRIMARY KEY (question_id, value)
);
CREATE TABLE IF NOT EXISTS gdai_question_option_translations (
    question_id VARCHAR(80) NOT NULL,
    value VARCHAR(80) NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    label VARCHAR(255) NOT NULL,
    PRIMARY KEY (question_id, value, language_code),
    FOREIGN KEY (question_id, value) REFERENCES gdai_question_options(question_id, value) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS gdai_garden_answers (
    photo_id UUID NOT NULL REFERENCES gdai_validated_photos(id) ON DELETE CASCADE,
    question_id VARCHAR(80) NOT NULL REFERENCES gdai_questions(id),
    answer_value TEXT NOT NULL,
    answered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (photo_id, question_id)
);

INSERT INTO gdai_questions(id,answer_type,required,display_order,feature_key) VALUES
('location','text',true,10,'location'),
('exposure','select',true,20,'exposure'),
('soil_type','select',true,30,'soil_type'),
('watering','select',true,40,'watering'),
('maintenance','select',true,50,'maintenance'),
('plant_style','select',true,60,'plant_style'),
('max_height_cm','number',false,70,'max_height_cm'),
('privacy_screen','boolean',true,80,'privacy_screen'),
('heat_tolerance','select',true,90,'heat_tolerance')
ON CONFLICT (id) DO NOTHING;
INSERT INTO gdai_question_translations(question_id,language_code,label) VALUES
('location','fr','Ville ou code postal'),('exposure','fr','Exposition au soleil'),
('soil_type','fr','Nature du sol'),('watering','fr','Arrosage souhaité'),
('maintenance','fr','Entretien accepté'),('plant_style','fr','Type de végétation'),
('max_height_cm','fr','Hauteur maximale des plantes (cm)'),
('privacy_screen','fr','Avez-vous besoin d’un brise-vue ?'),
('heat_tolerance','fr','Résistance à la chaleur souhaitée'),
('location','en','City or postal code'),('exposure','en','Sun exposure'),
('soil_type','en','Soil type'),('watering','en','Watering needs'),
('maintenance','en','Maintenance level'),('plant_style','en','Plant style'),
('max_height_cm','en','Maximum plant height (cm)'),
('privacy_screen','en','Do you need privacy screening?'),
('heat_tolerance','en','Desired heat tolerance')
ON CONFLICT DO NOTHING;
INSERT INTO gdai_question_rules(question_id,continent_code,climate_code,country_code)
VALUES ('heat_tolerance',NULL,'HOT_DRY',NULL);
INSERT INTO gdai_question_options(question_id,value,display_order) VALUES
('exposure','FULL_SUN',1),('exposure','PARTIAL_SHADE',2),('exposure','SHADE',3),
('soil_type','UNKNOWN',1),('soil_type','SANDY',2),('soil_type','LOAMY',3),('soil_type','CLAY',4),
('watering','LOW',1),('watering','MODERATE',2),('watering','REGULAR',3),
('maintenance','LOW',1),('maintenance','MODERATE',2),('maintenance','HIGH',3),
('plant_style','EVERGREEN',1),('plant_style','FLOWERING',2),('plant_style','MIXED',3),
('heat_tolerance','HIGH',1),('heat_tolerance','VERY_HIGH',2)
ON CONFLICT DO NOTHING;
INSERT INTO gdai_question_option_translations(question_id,value,language_code,label)
SELECT o.question_id,o.value,l.lang,
CASE o.value
WHEN 'FULL_SUN' THEN CASE WHEN l.lang='fr' THEN 'Plein soleil' ELSE 'Full sun' END
WHEN 'PARTIAL_SHADE' THEN CASE WHEN l.lang='fr' THEN 'Mi-ombre' ELSE 'Partial shade' END
WHEN 'SHADE' THEN CASE WHEN l.lang='fr' THEN 'Ombre' ELSE 'Shade' END
WHEN 'UNKNOWN' THEN CASE WHEN l.lang='fr' THEN 'Inconnu' ELSE 'Unknown' END
WHEN 'SANDY' THEN CASE WHEN l.lang='fr' THEN 'Sableux' ELSE 'Sandy' END
WHEN 'LOAMY' THEN CASE WHEN l.lang='fr' THEN 'Limoneux' ELSE 'Loamy' END
WHEN 'CLAY' THEN CASE WHEN l.lang='fr' THEN 'Argileux' ELSE 'Clay' END
WHEN 'LOW' THEN CASE WHEN l.lang='fr' THEN 'Faible' ELSE 'Low' END
WHEN 'MODERATE' THEN CASE WHEN l.lang='fr' THEN 'Modéré' ELSE 'Moderate' END
WHEN 'REGULAR' THEN CASE WHEN l.lang='fr' THEN 'Régulier' ELSE 'Regular' END
WHEN 'HIGH' THEN CASE WHEN l.lang='fr' THEN 'Élevé' ELSE 'High' END
WHEN 'EVERGREEN' THEN CASE WHEN l.lang='fr' THEN 'Persistant' ELSE 'Evergreen' END
WHEN 'FLOWERING' THEN CASE WHEN l.lang='fr' THEN 'Fleuri' ELSE 'Flowering' END
WHEN 'MIXED' THEN CASE WHEN l.lang='fr' THEN 'Mixte' ELSE 'Mixed' END
WHEN 'VERY_HIGH' THEN CASE WHEN l.lang='fr' THEN 'Très élevée' ELSE 'Very high' END
ELSE o.value END
FROM gdai_question_options o CROSS JOIN (VALUES ('fr'),('en')) AS l(lang)
ON CONFLICT DO NOTHING;
