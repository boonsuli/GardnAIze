# GardnAIze — Wiki développeur

> Guide de prise en main, architecture et démarrage local. Ce wiki est versionné dans `docs/` et accessible depuis la page d'accueil du dépôt. Il ne nécessite pas d'activer le GitHub Wiki séparé.

## 1. À quoi sert GardnAIze ?

GardnAIze aide un particulier à choisir des végétaux adaptés à son jardin à partir d'une **photo**, de sa **localisation** et d'un **questionnaire**. Le parcours cible est : dépôt de la photo → validation → questions et consentements → analyse visuelle → sélection de plantes compatibles → affichage des recommandations. L'édition d'une image avec les plantes proposées est une extension facultative.

Le MVP E2E vise une démonstration le **15 décembre 2026**. Le code est en cours d'intégration : un service disponible ne signifie pas que toute la chaîne de recommandation est déjà opérationnelle.

## 2. Architecture

```text
Navigateur
  └── GDAI-FRONT (Angular 21, :8080 via Docker)
        └── GDAI-BACK (Spring Boot 3.5.7 / Java 25, :8081)
              ├── PostgreSQL 18 (application)
              ├── GDAI-VALID (FastAPI / ResNet-18 V2)
              ├── GDAI-VISION (Gemini, analyse photo)
              ├── GDAI-PLANT (Random Forest + catalogue horticole)
              ├── GDAI-SEGMT (segmentation, optionnel)
              └── GDAI-GNERAT (édition image, optionnel)
  └── ai-service (:8000) : API FastAPI existante, adaptateur Vision
```

GDAI-BACK pilote les étapes de manière asynchrone (réponse HTTP 202 et consultation du statut). Le frontend ne doit pas appeler directement les fournisseurs d'IA ni exposer les clés API. Les notebooks KNN/K-Means servent à la classification et à l'exploration des images ; ils ne constituent pas à eux seuls le moteur final de recommandation.

| Module | Rôle | Documentation |
| --- | --- | --- |
| GDAI-FRONT | Saisie photo, questionnaire, consentements, résultats | [Frontend](../frontend/README.md) |
| GDAI-BACK | REST, orchestration master/worker, stockage | [Backend](../backend/README.md) |
| GDAI-VALID | Contrôle de photo en trois classes, ResNet-18 | [Validation](../validation/README.md) |
| GDAI-VISION | Analyse des éléments du jardin via Gemini | [AI service](../ai-service/README.md) |
| GDAI-PLANT | Compatibilité jardin/plantes, Random Forest | [Données ML](../database/README.md) |
| GDAI-SEGMT | Segmentation des zones, **optionnel pour le MVP** | [Validation et segmentation](../validation/README.md) |
| GDAI-GNERAT | Visualisation avec ajout de plantes, **optionnel** | [Vue d'ensemble](../README.md) |

## 3. Prérequis

- Git et Docker Engine / Docker Desktop en fonctionnement.
- **Docker Compose v2.24.4 ou supérieur** : `compose.local.yaml` utilise `!override`.
- Accès Internet pour construire les images et télécharger les dépendances.
- Ressources suffisantes pour Java, PostgreSQL et les services Python.
- Poids ResNet-18 V2 **non versionnés** : `models/weights/garden_resnet18_v2.pth`. Les métadonnées attendues sont `models/metadata/garden_resnet18_v2.json`. Sans les poids, le service de validation peut ne pas être prêt.
- **Clé API Google Gemini valide obligatoire pour l'analyse réelle des photos par GDAI-VISION et le parcours E2E complet.** La clé doit autoriser le modèle sélectionné, avec des quotas suffisants et, si nécessaire, une facturation activée. Sans clé, certains services locaux et endpoints de santé peuvent démarrer, mais l'analyse Vision ne fonctionnera pas normalement. Obtenir une clé sur [Google AI Studio](https://aistudio.google.com/apikey).

Images configurées : PostgreSQL `postgres:18-alpine`, Java d'exécution `amazoncorretto:25-alpine`. Le **numéro de version du moteur Docker** dépend de l'installation de l'utilisateur ; il n'est pas fixé par le dépôt.

### Configuration de Gemini pour le parcours complet

Dans le fichier local `.env` (jamais commité), renseigner :

```dotenv
GEMINI_API_KEY=votre_cle_api_gemini_valide
GEMINI_MODEL=gemini-3.8-flash
VISION_ENABLED=true
```

**Attention :** `gemini-3.8-flash` est la valeur actuellement proposée par le dépôt, mais sa disponibilité réelle doit être vérifiée auprès de l'API Gemini. Utiliser un identifiant de modèle accessible avec votre clé. Le backend possède également une variable `VISION_API_KEY` distincte ; vérifier sa configuration si l'intégration requiert une authentification supplémentaire. Ne jamais publier la clé dans Git, le Wiki ou les logs.

## 4. Démarrage local recommandé (Docker Compose)

Depuis la racine du dépôt :

```bash
git clone https://github.com/boonsuli/GardnAIze.git
cd GardnAIze
cp .env.example .env
# Modifier .env : au minimum DB_PASSWORD, puis la configuration Vision si souhaitée.
docker compose version
docker compose -f compose.yaml -f compose.local.yaml config --quiet
docker compose -f compose.yaml -f compose.local.yaml up --build -d --wait
docker compose -f compose.yaml -f compose.local.yaml ps
```

**Ne jamais commiter `.env`, les clés API, les photos privées ou les conversations ChatGPT.**

Paramètres utiles du fichier `.env` :

| Variable | Usage | Remarque |
| --- | --- | --- |
| `DB_PASSWORD` | Mot de passe PostgreSQL utilisé par Compose et le backend | Choisir une valeur locale ; une modification ultérieure ne réinitialise pas un volume existant |
| `FRONTEND_PORT` | Port de l'interface | 8080 par défaut |
| `BACKEND_PORT` | Port Spring Boot | 8081 par défaut |
| `DB_PORT` | Port PostgreSQL exposé en local | 5432 par défaut |
| `VALID_PORT` | Port de validation photo en local | 8001 par défaut |
| `GEMINI_API_KEY` | Clé d'appel Gemini pour ai-service | Secret ; ne pas publier |
| `GEMINI_MODEL` | Identifiant du modèle Gemini | Le dépôt propose `gemini-3.8-flash` ; **vérifier la disponibilité réelle auprès de l'API** avant démo |
| `VISION_ENABLED` | Active l'intégration Vision côté backend | `false` par défaut ; mettre `true` pour tester la chaîne Vision |
| `VISION_API_KEY` | Clé de configuration de l'intégration Vision du backend | Vérifier le contrat du fournisseur ; peut différer de `GEMINI_API_KEY` |

**GDAI-VISION est une brique fonctionnelle attendue du MVP, et non une fonctionnalité optionnelle du produit.** Le drapeau `VISION_ENABLED` sert à désactiver temporairement l'appel externe dans un environnement de développement. Ne pas confondre la configuration d'un modèle et la preuve d'une inférence réussie.

## 5. URLs et vérifications

| Service | URL locale |
| --- | --- |
| Interface | http://localhost:8080 |
| Backend Swagger | http://localhost:8081/swagger-ui.html |
| Backend santé | http://localhost:8081/actuator/health |
| AI service Swagger | http://localhost:8000/docs |
| AI service santé | http://localhost:8000/health |
| GDAI-VALID santé | http://localhost:8001/api/v1/health |
| GDAI-VALID Swagger | http://localhost:8001/docs |

```bash
curl -f http://localhost:8081/actuator/health
curl -f http://localhost:8000/health
curl -f http://localhost:8001/api/v1/health
docker compose -f compose.yaml -f compose.local.yaml logs --tail=100 backend ai-service gdai-valid
```

La réponse HTTP des endpoints de santé n'est **pas** une preuve que la recommandation Random Forest fonctionne de bout en bout. Vérifier également la présence du modèle ResNet, les migrations, les réponses métier et le parcours depuis le frontend.

## 6. Base de données horticole et ML

Le conteneur `postgres` sert la base applicative `gardnaize` ; les données horticoles utilisent la base logique `gardnaize_ml` et le schéma `horticulture`. Pour initialiser les migrations ML :

```bash
docker compose -f compose.yaml -f compose.ml.yaml --profile ml run --rm flyway-ml
```

Attention : `compose.ml.yaml` expose PostgreSQL sur le port hôte `5433` par défaut, tandis que `compose.local.yaml` l'expose sur `5432`. Ne pas lancer les configurations de manière contradictoire sur le même port. Voir [database/README.md](../database/README.md).

## 7. Arrêt, dépannage et sécurité

```bash
docker compose -f compose.yaml -f compose.local.yaml logs -f
docker compose -f compose.yaml -f compose.local.yaml down
```

**Ne pas utiliser `down -v`** sans vouloir supprimer les données PostgreSQL persistées.

- **Port occupé** : vérifier `docker compose ps` et les variables `*_PORT`.
- **Backend non prêt** : examiner les logs, les identifiants PostgreSQL et les migrations Flyway.
- **Validation non prête** : vérifier le fichier `.pth`, les métadonnées et les montages `models/`.
- **Gemini renvoie 404/503** : contrôler l'identifiant réel du modèle, la clé, les quotas et les logs. Le nom présent dans `.env` ne garantit pas sa validité auprès de Google.
- **Vision désactivée** : `VISION_ENABLED=false` est la valeur par défaut dans Compose.
- **Compose refuse `!override`** : mettre à jour le plugin Docker Compose.

Les fichiers locaux `docs/ChatGPT-conversation/` sont exclus de Git ; **ne pas les ajouter à la documentation publique**.

## 8. Développement hors Docker et documentation détaillée

Pour lancer Angular, Spring Boot et FastAPI séparément, consulter [deployment-local.md](deployment-local.md). Les exigences natives incluent Java 25, Maven 3.9+, Python 3.12, Node.js 22.12+ et PostgreSQL 18.

Autres références : [workflow photo / PR35](PHOTO_WORKFLOW_PR35.md), [déploiement local](deployment-local.md), [README principal](../README.md).

> Ce guide documente la configuration du dépôt ; aucune exécution Docker E2E n'est attestée par sa seule rédaction.
