<div align="center">
    <img src="../frontend/public/logo-gardnaize.svg" alt="GardnAIze — Imagine. Design. Grow." width="440" />
    <p><strong>GardnAIze · Java Backend REST API</strong></p>
    <p>
        <img alt="Java 25 LTS" src="https://img.shields.io/badge/Java-25%20LTS-ED8B00?logo=openjdk&logoColor=white" />
        <img alt="Amazon Corretto 25" src="https://img.shields.io/badge/Amazon%20Corretto-25-FF9900?logo=amazonaws&logoColor=white" />
        <img alt="Spring Boot 3.5.7" src="https://img.shields.io/badge/Spring%20Boot-3.5.7-6DB33F?logo=springboot&logoColor=white" />
        <img alt="Spring Data JPA" src="https://img.shields.io/badge/Spring%20Data-JPA-6DB33F?logo=spring&logoColor=white" />
        <img alt="Hibernate ORM (managed)" src="https://img.shields.io/badge/Hibernate-ORM%20(Boot%20managed)-59666C?logo=hibernate&logoColor=white" />
        <img alt="PostgreSQL 18" src="https://img.shields.io/badge/PostgreSQL-18-4169E1?logo=postgresql&logoColor=white" />
    </p>
    <p>
        <img alt="Maven 3.9.11" src="https://img.shields.io/badge/Maven-3.9.11-C71A36?logo=apachemaven&logoColor=white" />
        <img alt="springdoc OpenAPI 2.8.13" src="https://img.shields.io/badge/springdoc%20OpenAPI-2.8.13-85EA2D?logo=swagger&logoColor=black" />
        <img alt="Swagger UI" src="https://img.shields.io/badge/Swagger-UI-85EA2D?logo=swagger&logoColor=black" />
        <img alt="Flyway (Boot managed)" src="https://img.shields.io/badge/Flyway-Boot%20managed-CC0200?logo=flyway&logoColor=white" />
        <img alt="JUnit 5" src="https://img.shields.io/badge/JUnit-5-25A162?logo=junit5&logoColor=white" />
        <img alt="Mockito" src="https://img.shields.io/badge/Mockito-Unit%20Tests-6DB33F" />
        <img alt="Docker" src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" />
    </p>
</div>

> **Point E2E — 10/11/2026 :** GDAI-BACK est **propriétaire des contrats REST publics** et de leur documentation Swagger/OpenAPI ; Angular doit s'y aligner. Le workflow proposé est confirmation multipart → VALID → persistance uniquement si photo valide → questionnaire → VISION → PLANT → recommandations. Les DTO, codes HTTP, statuts asynchrones et propositions des PR #28/#29 doivent être vérifiés avant fusion ; le parcours IA complet n'est **pas** certifié opérationnel. [Plan de câblage et critères d'acceptation](../docs/E2E_READINESS_2026-11-10.md).

> Versions shown are the versions explicitly pinned in the backend POM or Dockerfile. Hibernate, Flyway, JUnit and Mockito are managed by the Spring Boot dependency BOM, so their precise resolved versions are not asserted here.

**Stack:** Java 25 LTS (Amazon Corretto runtime), Spring Boot 3.5.7, Spring Data JPA / Hibernate, PostgreSQL 18, Flyway and springdoc OpenAPI 2.8.13.

## Launch

From the repository root: `docker compose up --build -d --wait`. Open the app at http://localhost:8080 and Swagger at http://localhost:8081/swagger-ui.html. OpenAPI JSON: http://localhost:8081/v3/api-docs. Health: http://localhost:8081/actuator/health.

For local Maven: `cd backend && mvn test && mvn spring-boot:run`, with `DB_URL`, `DB_USER`, `DB_PASSWORD` set for an accessible PostgreSQL instance. The Compose database is not published on the host by default.

## Endpoints

- `POST /api/v1/gardens`: create metadata, e.g. `{"name":"Mon jardin","location":"Paris","exposure":"FULL_SUN","soilType":"LOAMY"}`
- `GET /api/v1/gardens`: list gardens
- `GET /api/v1/gardens/{id}`: get garden
- `GET /api/v1/gardens/{id}/recommendations`: Java calls FastAPI `POST /recommendations`; returns 3 **demo rule-based** suggestions, not ML predictions.

Exposure values: `FULL_SUN`, `PARTIAL_SHADE`, `SHADE`. Soil values: `SANDY`, `LOAMY`, `CLAY`, `UNKNOWN`.

## Design

Controllers → services → Spring Data JPA repositories → PostgreSQL 18. Flyway migrates the schema and Hibernate validates it. Java `RestClient` calls the AI service with connection/read timeouts. JPA/Hibernate is **blocking**; R2DBC is intentionally not mixed with Hibernate. The frontend uses an API proxy. The garden photo remains **browser-only** and is not sent to the backend. No authentication, file storage or ML model is implemented yet. The demo rules are not verified plant advice. Source indentation: 4 spaces.

## Durable photo processing — merged PR #35

The previous 10 November E2E notes above are historical. The backend now exposes `POST /api/v1/gardens/{gardenId}/photos` (multipart `file`, `description`, `answersJson`, `consentKey`) returning **202 Accepted** with `requestId`, and `GET /api/v1/gardens/{gardenId}/photo-requests/{requestId}` for polling. Consent and required answers are checked server-side. PostgreSQL holds the request, photo, module runs, history, owner, expiry, attempt count and generation.

The Master claims `ACCEPTED` rows using `FOR UPDATE SKIP LOCKED`; the worker executes VALID then VISION with separate executors. Heartbeats renew leases, generation-fenced transactional writes reject stale workers, and an expired lease is atomically quarantined with `LEASE_EXPIRED` audit. `RECONCILIATION_REQUIRED` is **not** an automatic provider retry. Segmentation parallelism and PLANT are separate work.

Read [full state machine, transition conditions, event list and crash tests](../docs/PHOTO_WORKFLOW_PR35.md). Tests: `PhotoWorkflowWorkerIT`, `PhotoWorkflowMasterIT`, `PhotoWorkflowFencingIT`; VALID/VISION HTTP endpoints are stubbed locally to avoid Gemini charges.
