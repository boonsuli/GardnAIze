# Plan du dernier lot de scénarios (V1)

Contrôle du consolidé `garden-scenarios-consolidated-v1.json` :
29 entrées, 27 CANDIDATE, 1 EXCLUDED_NEAR_DUPLICATE, 1 MANUAL_REVIEW_REQUIRED.

## Contrôles de similarité
- FR-PAR-01 / FR-TEM-001 : doublon proche déjà exclu.
- FR-TEM-009 / FR-TEM-012 : 8 attributs catégoriels communs, 10 cm de hauteur et 1°C d'écart. Conserver éventuellement les deux seulement si leur différence horticole (sol, situation, région) est explicitement justifiée.
- FR-TEM-019 : le terme RAIN_GARDEN est ambigu pour une dépression naturelle. Résoudre avant figer les 50.

## Cible

Objectif indicatif : 24 propositions nouvelles, sous réserve de 26 profils réellement distincts parmi les anciens. La génération ne garantit ni 24 acceptations ni 50 scénarios définitifs.

## Commande (appel Gemini payant uniquement sur initiative explicite de l'utilisateur)

Depuis `gdai-plant/` :

```bash
python -m matching.generate_garden_scenarios \
  --count 24 \
  --existing-json data/scenarios/garden-scenarios-consolidated-v1.json \
  --out data/scenarios/pilot-24-targeted-v1.2.json \
  --allow-paid-api \
  --confirm-api-spend I_AUTHORIZE_GEMINI_API_COST
```

Le prompt inclut les profils existants et la validation détecte les similarités fortes entre lots. Les nouveaux scénarios proches sont marqués REVIEW_REQUIRED, pas supprimés automatiquement.

Contrôler `summary`, `near_duplicate_pairs` et les `reviews`, puis procéder à la revue manuelle avant intégration. Le fichier consolidé existant reste inchangé.

**Important** : 50 scénarios synthétiques × 40 plantes = 2 000 couples possibles, mais cela ne crée aucune étiquette de compatibilité indépendante pour entraîner/évaluer un Random Forest.
