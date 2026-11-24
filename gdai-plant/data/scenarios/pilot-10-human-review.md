# Revue raisonnée du pilote Gemini — 23 novembre 2026

Source : `pilot-10-original.json` et `pilot-10-reviewed-v1.2.json`.
Revue manuelle de plausibilité, **pas** validation horticole indépendante.
Les 10 enregistrements sont `SYNTHETIC_AI`. Les températures sont des hypothèses de scénarios, non des mesures.

| ID | Décision | Justification et enrichissement à vérifier |
| --- | --- | --- |
| FR-PAR-01 | KEEP_PENDING_METADATA | Bordure francilienne plausible ; climat tempéré de transition, limon/terre franche évoqués ; confirmer texture et contexte |
| FR-BRE-02 | KEEP_PENDING_METADATA | Massif de limite de propriété maritime plausible ; humidité saisonnière et texture du sol non documentées |
| FR-AQU-03 | KEEP_PENDING_METADATA | Bordure sèche, drainante et ensoleillée plausible ; préciser la zone climatique non méditerranéenne et la texture sableuse/limoneuse |
| FR-CTR-04 | KEEP_PENDING_METADATA | Plantation au nord d'une façade plausible ; exposition FULL_SHADE à confirmer selon obstacles et saison |
| FR-EST-05 | KEEP_PENDING_METADATA | Climat semi-continental et gel plausible ; texture limoneuse évoquée, humidité à préciser |
| FR-NOR-06 | KEEP_PENDING_METADATA | Terrain en pente bien drainé plausible ; pluie régionale ne garantit pas eau disponible localement |
| FR-RHO-07 | KEEP_PENDING_METADATA | Cour lyonnaise ombragée et argile compactée plausible ; humidité et drainage doivent être distingués |
| FR-OCC-08 | KEEP_PENDING_METADATA | Bordure étroite et sèche plausible ; profondeur du substrat et situation climatique locale à préciser |
| FR-IDF-09 | KEEP_PENDING_METADATA | Noue recevant les eaux pluviales plausible ; différencier engorgement temporaire et permanent |
| FR-JUR-10 | EXCLUDE_MVP | Mention explicite de vallée jurassienne de moyenne altitude ; hors périmètre V1 non montagnard |

## Synthèse

- 9 propositions conservables pour enrichissement, 1 hors périmètre MVP.
- La validation automatisée v1.2 indique `REVIEW_REQUIRED` pour les 10 car les cinq nouveaux champs sont absents.
- Les 9 propositions conservables ne sont **pas** prêtes à alimenter le Random Forest.
- Ne pas déduire des observations de terrain à partir des descriptions synthétiques.
- Aucun nouvel appel Gemini nécessaire pour enrichir ou filtrer le pilote.

## Étape suivante

Enrichir hors ligne les 9 propositions avec `climate_zone`,
`terrain_type`, `soil_texture`, `soil_moisture_seasonality`,
`planting_context`, tout en marquant explicitement les valeurs supposées.
Repasser le validateur, puis inspecter la diversité des scénarios avant de
produire de nouvelles propositions. Préserver les fichiers bruts et les
décisions de revue séparément.
