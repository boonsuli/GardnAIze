# GDAI-FRONT — Angular user interface

![Angular](https://img.shields.io/badge/Angular-21-DD0031) ![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6) ![UI](https://img.shields.io/badge/UI-Angular%20Material-3F51B5)

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
