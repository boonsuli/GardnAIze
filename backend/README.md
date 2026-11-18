# GDAI-BACK — Spring Boot orchestration

<p align="left">
  <img alt="Language: Java 25" src="https://img.shields.io/badge/Language-Java%2025-ED8B00" />
  <img alt="Framework: Spring Boot 3.5" src="https://img.shields.io/badge/Framework-Spring%20Boot%203.5-6DB33F" />
  <img alt="API: REST + OpenAPI" src="https://img.shields.io/badge/API-REST%20%2B%20OpenAPI-85EA2D" />
  <img alt="Async: CompletableFuture" src="https://img.shields.io/badge/Async-CompletableFuture-7952B3" />
  <img alt="Database: PostgreSQL" src="https://img.shields.io/badge/Database-PostgreSQL-4169E1" />
  <img alt="Migrations: Flyway" src="https://img.shields.io/badge/Migrations-Flyway-CC0200" />
</p>

GDAI-BACK is the central application API and orchestrator. It receives requests from GDAI-FRONT, persists garden and photo information, coordinates AI processing and returns application-level statuses and results.

## Responsibilities

- Publish the REST/OpenAPI contract consumed by GDAI-FRONT.
- Validate uploads and questionnaire/consent submissions.
- Coordinate GDAI-VALID, optional GDAI-VISION and GDAI-PLANT asynchronously.
- Support local segmentation observations and optional GDAI-GNERAT image visualization without blocking plant recommendations.
- Persist garden metadata, workflow history and recommendations in PostgreSQL.
- Handle worker leases, state transitions and processing failures.

The merged photo workflow returns HTTP **202 Accepted** and exposes request-status polling. See [workflow and state machine](../docs/PHOTO_WORKFLOW_PR35.md) for exact endpoints, transitions and integration tests. The complete Random Forest and segmentation pipeline is not claimed operational.

## Run and inspect

```bash
docker compose up --build -d --wait
cd backend
mvn test
```

Swagger: http://localhost:8081/swagger-ui.html  
OpenAPI: http://localhost:8081/v3/api-docs  
Health: http://localhost:8081/actuator/health

**E2E demonstration objective:** 15 December 2026.

### Future commercial B2B API

Beyond its current internal orchestration API, GDAI-BACK may later expose a **paid, externally consumable B2B API** for garden analysis and personalized plant recommendations. This will complement the merchant Web connectors, enabling retailers and partners to develop their own user experiences. Subscription and usage-based pricing are options under consideration; public API contracts, authentication, usage metering, quotas and commercial terms are not yet defined or claimed to be implemented. This commercial API is outside the scope of the 15 December 2026 E2E demonstration.
