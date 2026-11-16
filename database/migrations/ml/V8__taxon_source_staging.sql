-- Source records are staged without promoting unverified horticultural attributes.
CREATE TABLE horticulture.ml_taxon_source_staging (
 source_key text NOT NULL,
 external_id text NOT NULL,
 scientific_name text NOT NULL,
 canonical_name text,
 source_url text NOT NULL,
 source_version text,
 retrieved_at timestamptz NOT NULL DEFAULT now(),
 payload jsonb NOT NULL,
 review_status text NOT NULL DEFAULT 'PENDING'
   CHECK (review_status IN ('PENDING','APPROVED','REJECTED')),
 PRIMARY KEY(source_key,external_id)
);
CREATE INDEX idx_taxon_staging_name ON horticulture.ml_taxon_source_staging(lower(scientific_name));
