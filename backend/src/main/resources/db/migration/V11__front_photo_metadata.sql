-- Extend the existing public application tables; do not duplicate photo storage.
ALTER TABLE public.garden_projects
    ADD COLUMN country_code VARCHAR(8) NOT NULL DEFAULT 'FR',
    ADD COLUMN climate_region VARCHAR(120) NOT NULL DEFAULT 'UNKNOWN';

ALTER TABLE public.garden_projects
    ADD CONSTRAINT chk_garden_country_code
    CHECK (country_code IN ('FR', 'BE', 'CH', 'ES', 'IT', 'OTHER'));

ALTER TABLE public.garden_photos
    ADD COLUMN description VARCHAR(1000) NOT NULL DEFAULT '';

-- Existing rows up to 10 MiB are retained; new uploads are limited in the service.
-- Do not reduce the existing file_size_bytes CHECK without a data migration.
COMMENT ON COLUMN public.garden_photos.description IS
    'User-confirmed garden photo description supplied by the frontend';
COMMENT ON COLUMN public.garden_projects.climate_region IS
    'User-selected climate region; UNKNOWN is not an inferred climate';
