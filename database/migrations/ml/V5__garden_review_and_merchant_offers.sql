-- Reviewed garden-image dataset and time-stamped merchant offers; separate ML database.
CREATE TABLE horticulture.garden_image_candidate (
 image_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 source_key text NOT NULL, external_id text NOT NULL,
 image_uri text NOT NULL, image_sha256 char(64),
 garden_group_key text NOT NULL,
 license_name text, redistribution_allowed boolean NOT NULL DEFAULT false,
 climate_zone text, soil_type text, exposure text,
 review_status varchar(12) NOT NULL DEFAULT 'PENDING'
   CHECK (review_status IN ('PENDING','ACCEPTED','REJECTED','UNCERTAIN')),
 review_reason text, reviewed_at timestamptz,
 dataset_split varchar(10) CHECK (dataset_split IN ('TRAIN','VAL','TEST')),
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(source_key,external_id),
 CHECK (dataset_split IS NULL OR review_status='ACCEPTED')
);
CREATE INDEX idx_garden_review_status ON horticulture.garden_image_candidate(review_status);
CREATE INDEX idx_garden_group ON horticulture.garden_image_candidate(garden_group_key);
CREATE TABLE horticulture.plant_merchant_offer (
 offer_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 plant_id bigint NOT NULL REFERENCES horticulture.plant(plant_id),
 data_source_id bigint NOT NULL REFERENCES horticulture.data_source(data_source_id),
 external_offer_id text NOT NULL,
 product_url text, price_amount numeric(12,2) CHECK (price_amount >= 0),
 currency char(3) NOT NULL DEFAULT 'EUR',
 pot_size_l numeric(9,2), height_cm integer,
 available boolean, observed_at timestamptz NOT NULL DEFAULT now(),
 raw_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
 UNIQUE(data_source_id,external_offer_id)
);
CREATE INDEX idx_merchant_offer_plant ON horticulture.plant_merchant_offer(plant_id);
