-- Forward-only schema rename. V10 remains unchanged for existing Flyway histories.
-- PostgreSQL preserves table data, indexes, constraints and foreign keys on schema rename.
-- Fail rather than overwrite an existing target schema.
DO $$
BEGIN
    IF to_regnamespace('gardnaize') IS NULL THEN
        RAISE EXCEPTION 'Expected legacy gardnaize schema from V10 is missing';
    END IF;
    IF to_regnamespace('app_schema') IS NOT NULL THEN
        RAISE EXCEPTION 'Target app_schema already exists; review manually before migration';
    END IF;
END
$$;

ALTER SCHEMA gardnaize RENAME TO app_schema;

COMMENT ON SCHEMA app_schema IS
'GardnAIze application domain: gardens, images, plant catalog, source provenance and recommendations';
