# GDAI-VALID — ResNet-18 V2

![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB) ![FastAPI](https://img.shields.io/badge/API-FastAPI-009688) ![ResNet-18 V2](https://img.shields.io/badge/Model-ResNet--18%20V2-EE4C2C) ![Three classes](https://img.shields.io/badge/Classes-3-7952B3) ![Docker](https://img.shields.io/badge/Deployment-Docker-2496ED)

[Wiki de démarrage local](../docs/WIKI.md)

## Objectif

GDAI-VALID est le service FastAPI de validation des photographies transmises par GDAI-BACK. Il classe les images en trois catégories :

- `garden` : photographie de jardin exploitable ;
- `not_garden` : photographie ne représentant pas un jardin ;
- `unusable` : photographie inexploitable.

La segmentation des zones du jardin est confiée au module distinct **GDAI-SEGMT**.

## Entraînement V2

Le modèle est un **ResNet-18** préentraîné avec `ResNet18_Weights.IMAGENET1K_V1`, puis adapté aux trois classes. La graine de reproductibilité est `42`.

| Indicateur | Résultat |
| --- | ---: |
| Images d'entraînement | 43 |
| Images de validation | 15 |
| Images de test | 14 |
| Total | **72** |
| Accuracy de validation | **93,33 %** (14/15) |
| Accuracy de test | **100 %** (14/14) |
| F1 macro rapporté | **1,00** |

**Limites :** l'objectif initial de 120 images n'a pas été atteint. Ces métriques, obtenues sur de petits ensembles, sont exploratoires et ne garantissent pas la performance en production. Les dérivés floutés sont réservés à l'entraînement. Le découpage est fondé sur les groupes (`group_based`).

### Artefacts

- Poids locaux (non versionnés dans Git) : `models/weights/garden_resnet18_v2.pth`
- Métadonnées versionnées : `models/metadata/garden_resnet18_v2.json`
- Découpage : `datasets/splits/garden_split_v2.csv` (à conserver selon la politique de provenance et de confidentialité du dépôt)
- Notebooks : `notebooks/validation/01_dataset_selection.ipynb` et `notebooks/validation/02_resnet18_training.ipynb` (adapter le nom du premier notebook au fichier effectivement conservé dans le dépôt)

Le modèle V1 est conservé. Les poids V2 doivent être installés séparément sur chaque environnement de déploiement.

## Service FastAPI

| Méthode | Endpoint | Fonction |
| --- | --- | --- |
| `POST` | `/api/v1/validation/photo` | Classification d'une photographie |
| `GET` | `/api/v1/health` | État du service et disponibilité du modèle |
| `GET` | `/api/v1/model/info` | Métadonnées du modèle chargé |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/redoc` | ReDoc |
| `GET` | `/openapi.json` | Contrat OpenAPI JSON |

Swagger UI et ReDoc sont deux présentations du même contrat OpenAPI, générées automatiquement par FastAPI ; elles ne nécessitent pas de maintenance documentaire distincte.

### Démarrage local

Depuis la racine du dépôt :

```bash
source .venv/bin/activate
cd validation
VALID_MODEL_PATH="../models/weights/garden_resnet18_v2.pth" \
VALID_METADATA_PATH="../models/metadata/garden_resnet18_v2.json" \
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Le port `8001` permet de tester V2 sans arrêter le conteneur existant exposé sur `8000`.

### Contrôles

```bash
curl -f http://127.0.0.1:8001/api/v1/health
curl -f http://127.0.0.1:8001/api/v1/model/info
curl -f http://127.0.0.1:8001/openapi.json
```

Attendu : `model_ready: true`, `ready: true`, `version: v2`, `architecture: resnet18`.

Des essais manuels dans Swagger ont été effectués avec une photographie de chacune des trois catégories. Les prédictions et seuils de confiance exacts ne sont pas consignés ici ; ils restent à vérifier dans le compte rendu des essais.

## Intégration Docker

Le déploiement doit fournir les chemins configurés par `VALID_MODEL_PATH` et `VALID_METADATA_PATH`, par exemple via des montages en lecture seule :

```yaml
volumes:
  - ./models/weights:/models/weights:ro
  - ./models/metadata:/models/metadata:ro
environment:
  VALID_MODEL_PATH: /models/weights/garden_resnet18_v2.pth
  VALID_METADATA_PATH: /models/metadata/garden_resnet18_v2.json
```

Ces chemins supposent un fichier Compose situé à la racine du dépôt. Vérifier les chemins et le nom réel du service avant modification. Un modèle non chargé doit être signalé par l'état `model_ready: false` et les requêtes d'inférence doivent retourner `503`.

## Critères de validation avant fusion

- [ ] Notebooks V2 et métadonnées ajoutés au commit, sans inclure les images dont la licence n'autorise pas la redistribution.
- [ ] Poids `.pth` exclus de Git et conservés localement / dans un stockage d'artefacts adapté.
- [ ] Configuration FastAPI V2 et montages Docker vérifiés.
- [ ] Tests automatisés FastAPI réussis ; le test d'indisponibilité du modèle simule explicitement son absence.
- [ ] Tests d'inférence réels vérifiés sur les trois classes.
- [ ] `GET /docs`, `/redoc`, `/openapi.json`, `/api/v1/health` et `/api/v1/model/info` validés.
- [ ] Vérification du contrat d'intégration GDAI-BACK → GDAI-VALID.
- [ ] CI de la Pull Request réussie.

## Suite du projet

Après validation de l'intégration et fusion de la PR, le développement peut se concentrer sur **GDAI-SEGMT**, service autonome de segmentation des zones du jardin. L'enrichissement du dataset GDAI-VALID jusqu'à 120 images, puis au-delà, reste une amélioration future distincte.
