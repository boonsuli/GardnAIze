# Revue du lot ciblé de 24 scénarios

Source : `pilot-24-targeted-v1.2.json` (22 ACCEPTED, 2 REVIEW_REQUIRED, 0 REJECTED).
Aucun scénario n'est une observation de terrain ou une étiquette de compatibilité plante.

## Décisions

- `FR-TEM-039` vs `FR-TEM-014` : faux positif du détecteur initial. L'un est en FULL_SHADE, l'autre FULL_SUN. Conserver les deux profils distincts. La détection exige désormais même exposition et même contexte.
- `FR-TEM-021` vs `FR-PAR-01` : profils proches, mais FR-TEM-021 a un drainage GOOD contre MODERATE, et un contexte régional différent. Garder REVIEW_REQUIRED jusqu'à arbitrage; ne pas modifier arbitrairement les valeurs pour obtenir ACCEPTED.
- `FR-TEM-009` vs `FR-TEM-012` (lot précédent) : différences de drainage, région et exposition contextuelle (façade vs chênaie), malgré de nombreux champs communs. Une variante peut être utile mais reste à documenter.
- `FR-TEM-019` : contexte RAIN_GARDEN pour une dépression naturelle, à clarifier.

## Comptage

29 précédents : 27 CANDIDATE, 1 exclu, 1 en revue.
24 nouveaux : 22 ACCEPTED, 2 en revue avec l'ancien détecteur.
Après correction du faux positif FR-TEM-039 : 50 candidats potentiels (27 + 22 + 1), sous réserve des revues encore ouvertes et de l'absence d'autres doublons.

## Vérification sans API

Depuis `gdai-plant/`, après récupération du code :

```bash
python -m unittest discover -s tests -p 'test_consolidate_garden_scenarios.py'
python -m matching.generate_garden_scenarios \
  --count 24 \
  --input-json data/scenarios/pilot-24-targeted-v1.2.json \
  --existing-json data/scenarios/garden-scenarios-consolidated-v1.json \
  --out data/scenarios/pilot-24-revalidated-v1.2.json
jq '.summary, .near_duplicate_pairs' data/scenarios/pilot-24-revalidated-v1.2.json
```

La revalidation ne consomme aucun crédit Gemini. Les fichiers sources restent inchangés.
