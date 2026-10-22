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

> **Status:** Initial Angular UI. Photo selection and local preview are available; server-side analysis, questionnaire and recommendation APIs are not connected yet.

## Purpose

The GardnAIze Angular application is the user-facing experience for a **standalone garden assistant**, designed for eventual integration into **plant retailers' websites** through a decoupled API architecture.

## Features

| Feature | Status |
| --- | --- |
| Responsive Angular Material home page with GardnAIze branding | Available |
| Select JPEG/PNG/WebP photo and preview locally | Available |
| Client-side file type and 10 MB size check | Available (server validation still required) |
| Configurable browser logging | Available |
| Backend photo upload and AI analysis | Planned |
| Garden questionnaire | Planned |
| Three recommended plants and explanations | Planned |
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
