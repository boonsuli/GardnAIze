
-- GDAI-PLANT V1
-- Source registry only: no plant data is imported.
-- NULL permissions mean "not yet verified", not "allowed".

INSERT INTO horticulture.data_source
    (source_name, base_url, license_name,
     commercial_reuse_allowed, redistribution_allowed)
VALUES
    ('GBIF', 'https://www.gbif.org/', NULL, NULL, NULL),
    ('Ellenberg Europe', 'https://zenodo.org/records/7427088', NULL, NULL, NULL),
    ('RHS', 'https://www.rhs.org.uk/', NULL, NULL, NULL),
    ('TRY Plant Trait Database', 'https://www.try-db.org/', NULL, NULL, NULL),
    ('Truffaut', 'https://www.truffaut.com/', NULL, NULL, NULL),
    ('AuJardin.info', 'https://www.aujardin.info/', NULL, NULL, NULL),
    ('Moquet Jardins', 'https://www.moquet-jardins.com/', NULL, NULL, NULL),
    ('Les Entreprises du Paysage', 'https://www.lesentreprisesdupaysage.fr/', NULL, NULL, NULL),
    ('Paysagiste.info', 'https://www.paysagiste.info/', NULL, NULL, NULL),
    ('Jardin de Chloé', 'https://www.jardindechloe.com/', NULL, NULL, NULL),
    ('Jardin Harmonie', 'https://jardin-harmonie.fr/', NULL, NULL, NULL),
    ('Jardin Sud', 'https://www.jardinsud.fr/', NULL, NULL, NULL),
    ('Projet Vert', 'https://www.projetvert.fr/', NULL, NULL, NULL),
    ('AD Magazine', 'https://www.admagazine.fr/', NULL, NULL, NULL),
    ('Homify', 'https://www.homify.fr/', NULL, NULL, NULL),
    ('YouTube', 'https://www.youtube.com/', NULL, NULL, NULL)
ON CONFLICT (source_name) DO NOTHING;
