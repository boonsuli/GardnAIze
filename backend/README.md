# GardnAIze Backend

**Java 25 LTS (Amazon Corretto runtime)** · Spring Boot **3.5.7** · Hibernate/JPA (version managed by Spring Boot) · PostgreSQL 18 · Flyway · Swagger UI (springdoc).

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
