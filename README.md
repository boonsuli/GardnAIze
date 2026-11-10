<div align="center">
  <img src="frontend/public/logo-gardnaize.svg" alt="GardnAIze — Imagine. Design. Grow." width="480" />
  <p><strong>AI-assisted garden analysis and plant recommendations</strong></p>
  <p><strong>MVP in development · Local-first · Alyra AI Development project</strong></p>
  <p>
    <img alt="Angular 21" src="https://img.shields.io/badge/Angular-21-DD0031?logo=angular&logoColor=white" />
    <img alt="Java 25 LTS" src="https://img.shields.io/badge/Java-25%20LTS-ED8B00?logo=openjdk&logoColor=white" />
    <img alt="Spring Boot 3.5.7" src="https://img.shields.io/badge/Spring%20Boot-3.5.7-6DB33F?logo=springboot&logoColor=white" />
    <img alt="PostgreSQL 18" src="https://img.shields.io/badge/PostgreSQL-18-4169E1?logo=postgresql&logoColor=white" />
    <img alt="Python 3.12" src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" />
    <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white" />
    <img alt="PyTorch" src="https://img.shields.io/badge/PyTorch-ResNet--18-EE4C2C?logo=pytorch&logoColor=white" />
    <img alt="Docker Compose" src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" />
  </p>
</div>

> **Point d'avancement — 10 novembre 2026 · Démo MVP visée le 15 décembre 2026.** Estimation de pilotage : **65 % global / 25 % chaîne IA E2E**, non issue de tests automatisés. Le parcours actuel fournit des recommandations **par règles de démonstration**. La validation ResNet-18, le câblage complet Gemini → PLANT et le Random Forest restent à prouver. **P0 : unifier les contrats REST** (BACK propriétaire d'OpenAPI, FRONT consommateur). [Voir l'audit, le câblage et les critères de recette](docs/E2E_READINESS_2026-11-10.md).

> **Status — MVP under development.** The web application, Java API, FastAPI service, PostgreSQL persistence and Docker stack are integrated for a **rule-based demonstration**. Image-classification experiments have been conducted in notebooks, but trained-model inference is **not yet connected** to the running application. The photo currently stays in the browser. This is **not a production-ready AI recommendation system**.

## What is GardnAIze?

GardnAIze aims to help users choose plants suited to their garden, local conditions and preferences. The MVP targets an end-to-end journey: upload a garden photo, check whether it is usable, confirm observations, answer a short questionnaire, and receive **three explained plant recommendations**.

The first delivery is a **standalone, locally runnable application**. Retailer embedding, user accounts, checkout and public cloud hosting are outside the initial MVP scope.

## Current implementation

| Component | Technology | Implemented today | Next milestone |
| --- | --- | --- | --- |
| [Frontend](frontend/) | Angular 21, Angular Material 21, TypeScript 5.9 | Responsive UI, local image preview, garden questionnaire and integration with Java project/recommendation APIs | Upload the photo and show real analysis and recommendation results |
| [Backend](backend/) | Java 25, Spring Boot 3.5.7, Spring Data JPA, Flyway | REST garden APIs, PostgreSQL persistence, Swagger, FastAPI orchestration | Secure photo upload, classifier invocation, expanded preferences and saved results |
| [AI service](ai-service/) | Python 3.12, FastAPI | Health/API endpoints, rule-based demonstration recommendations, optional external vision adapter | Load and serve trained ResNet-18; use real horticultural data |
| [Image research](notebooks/) | PyTorch, torchvision, scikit-learn, Jupyter | Image acquisition/review notebooks, KNN and K-Means research, ResNet-18 training and evaluation | Independent evaluation, model packaging and inference API |
| [Application database](backend/) | PostgreSQL 18, Spring Flyway | Garden/project persistence | Persist photo metadata, analysis status and recommendation history |
| [ML database](database/) | PostgreSQL 18, separate Flyway migrations | Separate `gardnaize_ml` database and `horticulture` schema; V1–V3 migrations | Ingest and validate a real botanical catalog |
| [Deployment](compose.yaml) | Docker Compose, Nginx, Docker images | Local frontend + backend + AI service + PostgreSQL | End-to-end tests with actual model inference |

**Important distinction:** the ML database schema exists, but the `horticulture.plant` table is not populated by the initial migrations. The current recommendation API returns three **demo-rule** suggestions, not predictions or catalog-backed recommendations.

## Target MVP workflow

```text
Angular: upload garden photo
    |
    v
Spring Boot: validate upload and manage garden project       [TO DO]
    |
    v
FastAPI: ResNet-18 garden / not_garden / unusable inference   [TO DO]
    |                          |
    | usable                   +--> ask for a new photo
    v
Optional Gemini vision analysis + user-confirmed preferences [PARTIAL]
    |
    v
Horticultural catalog: filter by climate, sun, soil, water    [TO DO]
    |
    v
Rank compatible plants and explain three suggestions         [TO DO]
    |
    v
Angular: display and persist recommendations                 [TO DO]
```

The **current runnable demo** covers project creation, questionnaire metadata and rule-based suggestions; it does not yet execute the entire workflow above.

## Machine learning and deep learning

### Image classification — ResNet-18

- `scripts/download_garden_images.py`: acquire candidate images with provenance and licensing metadata.
- `notebooks/07_review_garden_images.ipynb`: visual review and manual label corrections.
- `scripts/create_garden_split.py`: deterministic source-group-based train/validation/test assignment.
- `datasets/splits/garden_split_v1.csv`: versioned split manifest.
- `notebooks/04_explore_garden_images.ipynb`: explore the image dataset.
- `notebooks/05_train_garden_classifier.ipynb`: train a transfer-learning ResNet-18 classifier.
- `notebooks/06_evaluate_garden_classifier.ipynb`: evaluate held-out predictions.

The initial experiment used **84 images** across `garden`, `not_garden` and `unusable`: **68 training, 11 validation and 5 test images**. A local notebook run reported **5/5 correct test predictions**. This is a **very small exploratory test**, not evidence of generalization or production accuracy. Model weights and original photos are intentionally excluded from Git; the repository does **not** ship a ready-to-run trained classifier.

### Other algorithms

- **KNN:** supervised image-classification experiments in research notebooks; not yet part of the application API.
- **K-Means:** unsupervised image clustering experiments in research notebooks; not yet part of the application API.
- **Random Forest:** candidate for a future well-defined supervised horticultural task, subject to suitable labeled data; **not claimed as trained or deployed**.
- **Gemini:** optional external image-analysis provider, distinct from locally trained models; its availability depends on configuration and API access.

See [image acquisition](docs/garden-image-acquisition.md), [classifier research](docs/ml-garden-classifier.md) and [notebooks](notebooks/). Some detailed research documentation still needs updating to match the newer group-based split.

## Architecture

```text
Angular 21 / Nginx
        |
        v
Spring Boot 3.5.7 (Java 25) ------> PostgreSQL: gardnaize
        |
        v
FastAPI (Python 3.12) ------------> PostgreSQL: gardnaize_ml [catalog integration pending]
        |
        +--> Demo rule-based recommendations [current]
        +--> Gemini adapter [optional/configured]
        +--> ResNet-18 model inference [planned]
```

The application and ML databases are logically separate. Spring Boot owns application persistence; the ML schema is migrated independently. No cross-database foreign keys are used.

## Run locally

### Docker Compose — integrated demonstration

From the repository root:

```bash
cp .env.example .env
# Set DB_PASSWORD in .env; configure GEMINI_API_KEY only if needed.
docker compose up --build -d --wait
docker compose ps
```

| Service | URL |
| --- | --- |
| Angular application | http://localhost:8080 |
| Spring Boot Swagger UI | http://localhost:8081/swagger-ui.html |
| Spring Boot health | http://localhost:8081/actuator/health |
| FastAPI OpenAPI | http://localhost:8000/docs |
| FastAPI health | http://localhost:8000/health |

The standard Compose stack runs the application PostgreSQL database internally. For the separate ML database and local notebook access, follow [database setup](database/README.md) and the [local deployment guide](docs/deployment-local.md).

```bash
docker compose logs -f
docker compose down
```

**Do not run `docker compose down -v` unless you intend to delete persisted database volumes.** Keep API keys and credentials in local environment configuration, never in Git.

### Native development

See [local deployment modes](docs/deployment-local.md) for the Java 25, Python 3.12, Node.js 22 and PostgreSQL 18 setup.

## Available APIs

| API | Purpose | Status |
| --- | --- | --- |
| `POST /api/v1/gardens` | Create a garden project | Implemented |
| `GET /api/v1/gardens` | List projects | Implemented |
| `GET /api/v1/gardens/{id}` | Read project | Implemented |
| `GET /api/v1/gardens/{id}/recommendations` | Return three suggestions via FastAPI | Implemented, **demo rules** |
| FastAPI `POST /recommendations` | Rule-based suggestions | Implemented, **not ML** |
| FastAPI `POST /analyze` | External vision adapter | Implemented, configuration-dependent |
| FastAPI `POST /classify-garden` | ResNet-18 inference | **Planned; not implemented** |

## MVP roadmap

1. **Botanical catalog:** source, license, normalize and ingest a first usable plant dataset into `gardnaize_ml`.
2. **Classifier serving:** export/version ResNet-18 weights, implement preprocessing and a tested FastAPI inference endpoint.
3. **Photo workflow:** validate and upload images through Spring Boot; handle rejection, errors and optional vision observations.
4. **Real recommendations:** apply reliable horticultural compatibility filters and explain the top three results.
5. **Angular integration:** complete the upload → preferences → results user journey.
6. **Quality and delivery:** expand independent evaluation, add end-to-end tests, update research documentation and rehearse the local demo.

## CI/CD and deployment

[GitHub Actions](.github/workflows/ci-cd.yml) provides source checks, application tests, container builds and local-stack smoke tests. The repository also contains AWS deployment preparation using GitHub OIDC, ECR and EC2/SSM; **configuration and deployment are environment-dependent**, not evidence of a live public production service.

## Project scope, data and licensing

GardnAIze is developed as an Alyra AI-development project, with the MVP initially focused on European garden conditions. Botanical suitability depends on verified climate, soil, exposure and water information; image recognition alone cannot establish soil composition.

Photos, model weights and large raw datasets are excluded from version control. Review image provenance, attribution and dataset terms before reuse or redistribution. **No open-source license is granted unless a LICENSE file is added.**

See the [branding guide](docs/BRANDING.md) for the official logo and visual identity.
