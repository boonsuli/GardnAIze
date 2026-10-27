<div align="center">
  <img src="frontend/public/logo-gardnaize.svg" alt="GardnAIze — Imagine. Design. Grow." width="480" />
  <p><strong>AI-powered garden planning and plant recommendations</strong></p>
  <p>
    <img alt="Angular 21" src="https://img.shields.io/badge/Angular-21-DD0031?logo=angular&logoColor=white" />
    <img alt="Angular Material 21" src="https://img.shields.io/badge/Angular%20Material-21-3F51B5?logo=angular&logoColor=white" />
    <img alt="Java 25 LTS" src="https://img.shields.io/badge/Java-25%20LTS-ED8B00?logo=openjdk&logoColor=white" />
    <img alt="Spring Boot 3.5" src="https://img.shields.io/badge/Spring%20Boot-3.5-6DB33F?logo=springboot&logoColor=white" />
    <img alt="PostgreSQL 18" src="https://img.shields.io/badge/PostgreSQL-18-4169E1?logo=postgresql&logoColor=white" />
    <img alt="Docker Compose" src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" />
  </p>
  <p>
    <img alt="Python 3.12" src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" />
    <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-planned-009688?logo=fastapi&logoColor=white" />
    <img alt="scikit-learn" src="https://img.shields.io/badge/scikit--learn-ML-F7931E?logo=scikitlearn&logoColor=white" />
    <img alt="DuckDB" src="https://img.shields.io/badge/DuckDB-analytics-FFF000?logo=duckdb&logoColor=black" />
    <img alt="Gemini API" src="https://img.shields.io/badge/Gemini-vision-4285F4?logo=googlegemini&logoColor=white" />
  </p>
</div>

> **Project status:** V1 under development. Badges show selected technology versions or planned components, **not** a claim that every service is implemented or deployed.

## Overview

**GardnAIze** helps people design a greener outdoor space. Users upload a garden photo, confirm the scene analysis, answer a short questionnaire (location, sunlight, soil, watering and preferences), and receive **three plant suggestions** with clear explanations and constraints.

The first release is designed to run **locally as a standalone application**. The architecture also anticipates future **embedding into plant retailers' websites**, using versioned APIs and a decoupled recommendation service. Commercial integrations, checkout, user accounts and cloud deployment are **not part of V1**.

## Local deployment options

- **Docker Compose (recommended):** `docker compose -f compose.yaml -f compose.local.yaml up --build -d --wait` (requires Docker Compose v2.24.4+).
- **Without Docker:** run PostgreSQL 18, FastAPI, Spring Boot and Angular natively in separate terminals.

See [Local deployment guide and cost-conscious AWS options](docs/deployment-local.md) for setup, ports, credentials, health checks, shutdown and infrastructure tradeoffs.

## Application components

| Directory | Technology | Responsibility | V1 status |
| --- | --- | --- | --- |
| [`frontend/`](frontend/) | Angular 21, Angular Material 21, TypeScript 5.9 | Responsive photo-upload interface, questionnaire and recommendations | Initial UI available; API integration pending |
| [`backend/`](backend/) | Java 25 LTS, Spring Boot 3.5 | REST orchestration, input validation, photo storage, questionnaire persistence and external vision API | Planned |
| [`ai-service/`](ai-service/) | Python 3.12, FastAPI, scikit-learn, TensorFlow/Keras | Plant similarity, clustering, botanical attribute prediction and garden-image classification | Planned |
| [`datasets/`](datasets/) | CSV / Parquet, pandas, DuckDB, SQL | Data ingestion, cleaning, deduplication, provenance and evaluation datasets | Structure prepared |
| [`models/`](models/) | scikit-learn, Keras | Exported, versioned ML/DL artifacts (large binaries excluded from Git) | Structure prepared |
| [`database/`](database/) | PostgreSQL 18, Flyway | Persistent plant catalog, garden projects, answers and photo metadata | Planned |
| [`docker/`](docker/) / `compose.yaml` | Docker Compose | Local multi-service deployment | Skeleton only |
| [`docs/`](docs/) | Markdown | Architecture, experiments, API contracts and operational notes | Structure prepared |

## Artificial intelligence

**Computer vision:** a small TensorFlow/Keras CNN (with a transfer-learning comparison) is planned to identify whether an uploaded image is a usable garden scene. A Gemini vision API integration can provide richer structured observations; it is an **external model**, separate from GardnAIze's trained models.

**Botanical recommendations:** deterministic filters first exclude incompatible plants (hardiness, exposure, water and space). scikit-learn nearest-neighbor search then ranks suitable plants. **K-Means** explores botanical clusters and can support diversity analysis. **Random Forest** may predict missing botanical care attributes *only when sufficiently reliable labeled examples exist*; predicted values must be marked as estimates and cannot silently replace verified facts.

**Data engineering:** Python pipelines ingest and normalize botanical sources; DuckDB/SQL window functions support quality checks and deduplication. Jupyter notebooks document preprocessing, visualization, evaluation and reproducible training. A labeled garden-image dataset is required for training the CNN.

## Intended user journey (V1)

1. Upload a garden photo (JPEG, PNG or WebP).
2. Validate image quality and suitability; analyze visible garden features.
3. Confirm observations and answer a short structured questionnaire.
4. Filter the botanical catalog and rank candidates using ML.
5. Display **three plants**, with reasons and cautions.

## Development and logging

The Angular starter can be run today:

```bash
cd frontend
npm install
npm start
```

Open http://localhost:4200. The frontend currently previews a selected photo; **end-to-end recommendations are not implemented yet**. See [frontend/README.md](frontend/README.md).

Each backend service will write configurable-level logs to stdout/stderr; Angular logs remain in browser DevTools. The intended levels are `DEBUG`, `INFO`, `WARN`, `ERROR`, `OFF` (subject to each framework's conventions). Docker Compose logs will be sufficient for the local V1; an ELK stack is deliberately out of scope.

## Future integration

The long-term goal is to expose stable, documented REST APIs for two distribution models: a **standalone consumer application** and an **embedded plant-retailer experience**. Tenant isolation, authentication, commercial catalog matching, consent, licensing and operational scaling will be addressed before production integration.

## License and botanical data

No open-source license is granted unless a `LICENSE` file is added. Botanical source terms, image rights and third-party API data policies must be checked before redistribution or commercial use.

## Dockerized local V1 (current scaffold)

The repository includes multi-stage container builds for the **Angular frontend** (Node.js 22 build stage, Nginx runtime) and the **FastAPI AI service** (Python 3.12, Uvicorn). Spring Boot, PostgreSQL and actual AI inference are **not yet included in the runnable Compose stack**.

Requirements: Docker Engine with Docker Compose v2.

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f
docker compose down
```

| Component | Local URL | What works today |
| --- | --- | --- |
| Frontend | http://localhost:8080 | Angular UI, local photo preview |
| AI service | http://localhost:8000/docs | FastAPI OpenAPI interface |
| AI health | http://localhost:8000/health | Health endpoint |

Use `AI_LOG_LEVEL=DEBUG docker compose up --build` for verbose Python logs. Docker rotates stdout/stderr logs (10 MB × 3 files per service). Browser-side Angular logs remain in browser DevTools. Ports can be changed with `FRONTEND_PORT` and `AI_PORT` environment variables. The AI API is bound to localhost in Compose.

The frontend and AI API currently run as **separate services**, not as an integrated recommendation workflow. The backend will orchestrate calls to the AI service when implemented.

## CI/CD pipeline and AWS deployment preparation

The workflow [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) runs on pull requests and pushes to `main`:

1. Verify **4-space indentation** in frontend and AI source files (tabs forbidden).
2. Run **Angular/TypeScript unit tests** and production build.
3. Run **FastAPI/Python unit tests** with pytest.
4. Build the frontend and AI Docker images, launch them with Docker Compose and run **integration smoke tests** against the web UI, health endpoint and OpenAPI document.
5. On successful `main` pushes, **optionally** authenticate to AWS using GitHub OIDC and push versioned images to **Amazon ECR**. Publishing is disabled until AWS has been configured.

### Future AWS ECR configuration

When the AWS account is available:

- Create private ECR repositories `gardnaize-frontend` and `gardnaize-ai-service` in the chosen region (default: `eu-west-3`).
- Configure an IAM role trusted by GitHub Actions OIDC, restricted to the repository and `main` branch, with permissions to upload images to those two repositories.
- Add GitHub repository **Actions variables**: `AWS_DEPLOY_ENABLED=true`, `AWS_ROLE_ARN=<role ARN>`, and optionally `AWS_REGION=eu-west-3`.
- Do **not** store AWS access keys in GitHub. The workflow requests short-lived credentials via OIDC and never publishes from pull requests.

Publishing images to ECR does **not** deploy them to ECS, App Runner or EC2; deployment will be a later step. The Spring Boot backend is not yet part of the runnable stack. When added, its Docker build will use **Amazon Corretto (Java 25 LTS)** and receive its own build, test, integration and ECR publishing jobs.

The repository stores readable source code with four-space indentation. Minification is reserved for generated production bundles inside the Docker build, not committed source files.

> Official GardnAIze logo reference and usage: [Branding guide](docs/BRANDING.md).

## Implemented Java backend and integrated demo

The [Java 25 backend](backend/README.md) provides Spring Boot 3.5.7, Hibernate/JPA, Flyway, PostgreSQL 18, Swagger UI and REST APIs consumed by Angular. Java calls FastAPI for **rule-based demonstration** recommendations, not trained ML predictions. Run `docker compose up --build -d --wait` and open http://localhost:8080. Swagger: http://localhost:8081/swagger-ui.html. Database is private to the Compose network. Set a strong `DB_PASSWORD` before any nonlocal deployment. The photo remains browser-only; persistence currently covers questionnaire metadata, not image bytes. GitHub Actions builds/tests Java and can publish `gardnaize-backend` to ECR once AWS OIDC is configured.
