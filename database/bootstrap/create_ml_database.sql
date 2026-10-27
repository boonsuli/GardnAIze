-- psql-only cluster bootstrap (not a Flyway migration).
SELECT 'CREATE DATABASE gardnaize_ml OWNER gardnaize' WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname='gardnaize_ml')
\gexec
