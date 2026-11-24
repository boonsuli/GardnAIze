# GDAI-FRONT — Angular user interface

<p align="left">
  <img alt="Frontend: Angular 21" src="https://img.shields.io/badge/Frontend-Angular%2021-DD0031" />
  <img alt="Language: TypeScript" src="https://img.shields.io/badge/Language-TypeScript-3178C6" />
  <img alt="UI: Angular Material" src="https://img.shields.io/badge/UI-Angular%20Material-3F51B5" />
  <img alt="Deployment: Docker Compose" src="https://img.shields.io/badge/Deployment-Docker%20Compose-2496ED" />
  <img alt="API: REST" src="https://img.shields.io/badge/API-REST-009688" />
  <img alt="i18n: FR + EN" src="https://img.shields.io/badge/i18n-FR%20%2B%20EN-7952B3" />
</p>

[Wiki de démarrage local](https://github.com/boonsuli/GardnAIze/wiki)

GDAI-FRONT provides the user journey for GardnAIze: garden photo upload/capture, metadata confirmation, questionnaire, consent, processing status and plant recommendations. The product is designed both for **individual gardeners (B2C)** and for potential **integration into garden retailer and plant e-commerce websites (B2B)**. Retailer embedding is a product direction, not a currently certified integration.

The frontend communicates **only with GDAI-BACK**. It does not invoke ResNet-18, segmentation, Gemini or Random Forest directly, and does not contain provider credentials.

## Main capabilities

- JPEG/PNG/WebP photo selection with a 5 MiB application limit.
- Garden location, optional description and confirmation.
- Multilingual FR/EN questionnaire and distinct consents for external analysis and training-data reuse.
- Asynchronous request submission and backend status polling.
- Presentation of recommendations and optional visualization when available.

The merged asynchronous workflow is documented in [PHOTO_WORKFLOW_PR35.md](../docs/PHOTO_WORKFLOW_PR35.md). Legacy demonstration rules and full AI-backed recommendations are distinct; the latter are not claimed as fully integrated.

## Local development

```bash
cd frontend
npm install
npm start
npm run test:unit
npm run build
```

Local UI: http://localhost:4200. Docker/Nginx UI: http://localhost:8080.

**E2E demonstration objective:** 15 December 2026. This date describes the intended demonstration, not the readiness of each capability.

### Future B2B embedded experience

A future version of GardnAIze may be embedded into merchant websites through **Web connectors**, allowing customers to receive garden-specific recommendations and an **editable, pre-filled basket** of plants and useful gardening products (soil, mulch, tools and watering supplies). Basket transfer and checkout would remain under the merchant's control. **No Web connector, merchant basket synchronization or checkout integration is claimed as implemented in the current MVP.**

The future B2B offer also includes a **paid API** for merchants and third-party developers building their own interfaces. This is distinct from the ready-to-embed Web connector offer and is not yet commercially available.
