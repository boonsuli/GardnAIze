<div align="center">
  <img src="public/logo-gardnaize.svg" alt="GardnAIze — Imagine. Design. Grow." width="360" />
  <p><strong>Responsive garden planning frontend</strong></p>
  <p>
    <img alt="Angular 21" src="https://img.shields.io/badge/Angular-21-DD0031?logo=angular&logoColor=white" />
    <img alt="Angular Material 21" src="https://img.shields.io/badge/Material-21-3F51B5?logo=angular&logoColor=white" />
    <img alt="TypeScript 5.9" src="https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript&logoColor=white" />
    <img alt="Node.js 22" src="https://img.shields.io/badge/Node.js-22-339933?logo=nodedotjs&logoColor=white" />
  </p>
</div>

> **Point E2E — 10/11/2026 :** le FRONT doit consommer le contrat OpenAPI publié par GDAI-BACK, sans définir seul les routes. Les workflows photo/confirmation/questionnaire des PR #26, #27 et #29 doivent être réconciliés avec `main` avant fusion. Cible : contrôle JPEG/PNG/WebP ≤ 1 MiB, pas de stockage Node `images-upload`, confirmation puis réponse VALID, questionnaire asynchrone, affichage des trois recommandations avec provenance. **Ces changements ne sont pas attestés comme intégrés dans `main`.** [Plan et contrats proposés](../docs/E2E_READINESS_2026-11-10.md).

> **Status:** Initial Angular UI. Photo selection and local preview are available; server-side analysis, questionnaire and recommendation APIs are not connected yet.

> **Mise à jour FRONT — 10 novembre 2026.** Les évolutions proposées dans les PR [#33](https://github.com/boonsuli/GardnAIze/pull/33), [#34](https://github.com/boonsuli/GardnAIze/pull/34) et [#36](https://github.com/boonsuli/GardnAIze/pull/36) couvrent : prise de photo smartphone ou sélection galerie, JPEG/PNG/WebP jusqu'à **5 Mio**, formulaire **pays obligatoire + ville/code postal obligatoire + région climatique facultative + description facultative (1 000 caractères)**, écran de confirmation et modification, puis transmission multipart `photo`, `countryCode`, `city`, `climateCode`, `description` vers GDAI-BACK. **Ces fonctionnalités sont décrites dans les PR ; leur fusion et leur fonctionnement E2E ne sont pas certifiés par cette mise à jour documentaire.** La persistance après VALID, le contrat Python `/validate` et l'enchaînement VISION → PLANT restent à valider. Pas de GPS ni d'API météo pour le MVP.

## Purpose

The GardnAIze Angular application is the user-facing experience for a **standalone garden assistant**, designed for eventual integration into **plant retailers' websites** through a decoupled API architecture.

## Features

| Feature | Status |
| --- | --- |
| Responsive Angular Material home page with GardnAIze branding | Available |
| Select JPEG/PNG/WebP photo and preview locally | Available |
| Client-side JPEG/PNG/WebP and 5 MiB limit | Proposed in PR #33; verify merged code and server validation |
| Configurable browser logging | Available |
| Photo multipart submission after confirmation | Proposed in PR #36; VALID contract and E2E pending |
| Country/city/climate/description input and confirmation | Proposed in PR #34; demo questionnaire retained |
| Three recommended plants and explanations | Demo-rule path; real AI pending |
| Embeddable retailer integration | Future |

## Technology and structure

- **Angular 21** standalone components, strict TypeScript **5.9**, Angular Material **21**.
- **Node.js 22** for development; production image will be built and served via Docker/Nginx.
- `src/app/app.component.*`: landing page and photo preview.
- `src/app/core/logger.service.ts`: browser logging with `DEBUG`, `INFO`, `WARN`, `ERROR`, `OFF`.
- `public/logo-gardnaize.svg`: reusable vector brand asset.

## Run locally

Prerequisites: Node.js **22** and npm.

```bash
cd frontend
npm install
npm start
```

Open **http://localhost:4200**.

```bash
npm run build
```

The project does not yet include a committed `package-lock.json`; generate it with `npm install` and commit it once dependency resolution is validated in CI.

## Logging

`LoggerService` defaults to `INFO` and can be configured at runtime with `setLevel("DEBUG")` or `setLevel("ERROR")`. Logs appear in **browser DevTools**, not automatically in Docker backend logs. Avoid logging images, personal data, tokens or full API responses.

## Planned API integration

The Angular app will communicate with the Spring Boot REST backend; Spring Boot will orchestrate the FastAPI recommendation service, PostgreSQL and external image analysis. Angular will not call private AI APIs with embedded secrets.

## Product direction

V1 prioritizes a short photo → questionnaire → recommendation journey. Future consumer and retailer deployments will reuse the same UI components and versioned API contracts, with deployment-specific branding and integration handled separately.

## Docker image (Angular + Nginx)

The multi-stage [Dockerfile](Dockerfile) builds Angular with **Node.js 22** and serves the static bundle using **Nginx Alpine** on port **8080**. The container does not require Node.js at runtime. The Nginx configuration supports Angular client-side routes with a fallback to `index.html` and writes access/error logs to stdout/stderr.

From the repository root:

```bash
docker compose up --build -d
docker compose logs -f frontend
```

Open **http://localhost:8080**. For frontend-only operation:

```bash
docker build -t gardnaize-frontend ./frontend
docker run --rm -p 8080:8080 gardnaize-frontend
```

The browser application is currently a standalone photo-preview interface. Angular's `LoggerService` logs in browser DevTools; Nginx access logs are visible through Docker. The future Spring Boot API must be configured separately; no backend API proxy is enabled yet.

## Automated unit tests and formatting

Run `npm run test:unit` to test photo-validation rules with Node's built-in test runner via `tsx`. GitHub Actions runs these tests and `npm run build` before Docker integration checks. TypeScript, HTML and SCSS sources use **four spaces**, with no tabs. Production bundles are minified during build only, not committed to Git.

> Official GardnAIze logo reference and usage: [Branding guide](../docs/BRANDING.md).

## Backend integration

The questionnaire now creates projects through `POST /api/v1/gardens` and requests demo suggestions through `GET /api/v1/gardens/{id}/recommendations`. Angular dev server proxies `/api` to http://localhost:8081; Docker Nginx proxies to the backend container. The photo is **not uploaded**; suggestions are explicitly rule-based placeholders pending actual ML inference.

## Async photo processing — merged PR #35

The older initial-UI notes above are historical. GDAI-FRONT now uses GDAI-BACK for photo preflight, questionnaire, explicit FR/EN external-processing consent and async submission. After consent, it submits the photo and answers to BACK, receives HTTP **202** and a durable `requestId`, then polls the BACK request endpoint. It stops on `COMPLETED`, `FAILED`, `REJECTED` or `RECONCILIATION_REQUIRED` (an expired worker lease requiring review). FRONT must not know or call VALID, VISION or Gemini directly.

The questionnaire catalog v2 and FR/EN dictionaries include `matureSpread` (adult canopy width) and `rootSpace` (root growth clearance). The legacy rule-based recommendation screen remains distinct from the new VALID/VISION request workflow. For status transitions, consent contract and observability, see [PR #35 workflow](../docs/PHOTO_WORKFLOW_PR35.md).
