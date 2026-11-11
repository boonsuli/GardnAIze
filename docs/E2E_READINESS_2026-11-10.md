# GardnAIze — E2E readiness and REST contract alignment
Updated: 2026-11-10. Target MVP demo: 2026-12-15.

> Planning snapshot, not proof of successful integration. Estimates are subjective: overall project ~65%; target AI end-to-end chain ~25%. The existing runnable path returns **demo-rule** plant suggestions, not ResNet-18/Random Forest predictions.

## Module readiness (planning estimates, not test coverage)

| Module | Estimate | Evidence / missing proof |
| --- | ---: | --- |
| GDAI-FRONT | 80% | Angular preview and demo questionnaire; proposed upload/confirmation changes in PRs #26/#27/#29 must be reconciled |
| GDAI-BACK | 75% | Garden REST/JPA/Flyway and demo recommendation orchestration; proposed photo/validation DTOs in PRs #28/#29 need alignment |
| GDAI-VALID | 55% | ResNet-18 notebooks; no packaged trained weights or tested inference endpoint in main |
| GDAI-VISION | 70% | Optional Gemini adapter exists; real response/error handling and wiring need verification |
| GDAI-PLANT | 25% | Demo rules exist; supervised Random Forest model and real catalog-backed ranking are not available |
| PostgreSQL/Flyway | 70% | App and ML schema foundations; real licensed plant catalog not ingested |
| Docker/CI | 80% | Four-service local stack; full target workflow not E2E tested |

## Contract ownership

**GDAI-BACK owns the public /api/v1 REST contracts and OpenAPI specification.** GDAI-FRONT consumes them through typed Angular services. Python services expose private contracts consumed only by BACK. Do not duplicate orchestration or expose Gemini secrets in the browser.

## Target flow (design, not implemented claim)

1. FRONT locally checks JPEG/PNG/WebP and max 1 MiB; previews photo and editable description.
2. User confirms. FRONT sends photo + description to BACK once.
3. BACK invokes VALID with temporary photo bytes. VALID responds with an explicit classification (`garden`, `not_garden`, `unusable`), confidence, model version and request ID. Threshold and response schema must be agreed and tested.
4. Invalid/unusable: BACK returns a typed rejection; no persistent photo record; FRONT shows "Photo non valide" and allows retry.
5. Valid: BACK persists photo + description in the application DB, then exposes the questionnaire; FRONT displays status and loads questions asynchronously after approximately 2 seconds.
6. FRONT submits answers; BACK validates and persists country, climate region and answers. Translation labels are application properties, not translated database rows.
7. BACK calls VISION (Gemini) and normalizes JSON; then calls PLANT with observations + questionnaire + botanical catalog context.
8. BACK persists and returns three explained recommendations; FRONT renders them. Until real PLANT is ready, demo rules must be **visibly labelled as a fallback**, never as Random Forest output.

## Proposed public endpoints — MUST VERIFY before implementation

These paths are **proposals**, not assertions that they exist in main:
- `POST /api/v1/gardens/photos/confirm` — multipart photo + description, validation outcome and garden ID only if accepted.
- `GET /api/v1/gardens/{id}/questions` — language-aware labels, stable question/option IDs.
- `POST /api/v1/gardens/{id}/answers` — validated answer IDs and user context.
- `POST /api/v1/gardens/{id}/analysis` — idempotent analysis start, status/error contract.
- `GET /api/v1/gardens/{id}/recommendations` — three recommendations and provenance (`demo-rules` or actual model/version).

Existing endpoints `POST /api/v1/gardens`, `GET /api/v1/gardens`, `GET /api/v1/gardens/{id}` and `GET /api/v1/gardens/{id}/recommendations` must remain compatible or be explicitly migrated. Decide synchronous vs async validation, polling/status URLs, HTTP 202/4xx semantics and request/response DTOs **before** changing either client.

## Priority backlog and acceptance gates

- **P0 contract:** inspect main and PRs #26–#30; write one versioned OpenAPI contract, examples, errors and status lifecycle; align BACK first, then FRONT. Do not merge drafts blindly.
- **P0 VALID:** export/version actual weights, build FastAPI inference, test valid/invalid/unusable, size and format failures.
- **P0 photo persistence:** no Node `images-upload` storage; persist only after positive validation; verify rollback/error cases.
- **P0 demo recommendations:** ingest a small licensed and reviewed plant catalog, apply deterministic climate/soil/exposure filters, label rule-based mode.
- **P1 VISION:** normalize Gemini JSON, handle 429/503/timeouts and missing API key without blocking a fallback demo.
- **P1 PLANT RF:** only train/evaluate if labeled supervised examples are sufficient; never present heuristic results as RF predictions.
- **P0 E2E:** Docker startup, OpenAPI docs, browser happy path, rejected photo retry, answer submission, 3 results, persistence, no duplicate uploads, CI green (including four-space checks).

## Suggested milestones

- Nov 10–13: freeze REST contracts and reconcile PRs.
- Nov 14–18: VALID serving and BACK integration.
- Nov 19–23: VISION response normalization and error handling.
- Nov 24–30: real starter catalog + deterministic recommendations.
- Dec 1–5: RF only if training data supports it.
- Dec 6–10: E2E tests and fixes.
- Dec 11–14: demo rehearsal and release freeze.
- Dec 15: target MVP demonstration.

## Verification commands (not executed by this documentation change)

```bash
docker compose config --quiet
docker compose up --build -d --wait
docker compose ps
curl -f http://localhost:8081/actuator/health
curl -f http://localhost:8000/health
curl -f http://localhost:8081/v3/api-docs
cd backend && mvn test
cd ../frontend && npm run test:unit && npm run build
cd ../ai-service && python -m pytest -q tests
```

Keep PRs in draft until their checks and integration evidence pass. No AWS deployment is needed for the Alyra MVP demo.
