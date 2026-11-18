<div align="center">
  <img src="frontend/public/logo-gardnaize.svg" alt="GardnAIze" width="460" />
  <p><strong>Imagine. Design. Grow.</strong></p>
  <p>AI-assisted garden analysis and personalized plant recommendations</p>
  <p>![DL](https://img.shields.io/badge/DL-ResNet----18-EE4C2C) ![Segmentation](https://img.shields.io/badge/Segmentation-DeepLabV3%20(candidate)-7952B3) ![ML](https://img.shields.io/badge/ML-KNN-3776AB) ![ML](https://img.shields.io/badge/ML-K----Means-3776AB) ![ML](https://img.shields.io/badge/ML-Random%20Forest-228B22) ![Vision](https://img.shields.io/badge/Vision-Gemini%20optional-4285F4)</p>
  <p>![Frontend](https://img.shields.io/badge/Frontend-Angular%2021-DD0031) ![Backend](https://img.shields.io/badge/Backend-Spring%20Boot%203.5-6DB33F) ![AI API](https://img.shields.io/badge/AI%20API-FastAPI-009688) ![Database](https://img.shields.io/badge/Database-PostgreSQL-4169E1) ![Deployment](https://img.shields.io/badge/Deployment-Docker-2496ED)</p>
</div>

## Overview

GardnAIze is an AI-powered garden recommendation product designed for **individual gardeners (B2C)** and **garden retailers, nurseries and e-commerce platforms (B2B)**. Individuals can analyze their garden and discover suitable plants; merchants can eventually integrate personalized recommendations into their online shopping experience. The project is currently developed as part of the Alyra AI Development program.

**Demonstration objective:** an integrated end-to-end (E2E) MVP demonstration on **15 December 2026**, as a technical validation milestone toward a commercial product. This is not a product launch date or a claim that the entire AI pipeline is already operational.

## Product audiences and distribution

- **B2C — Individual gardeners:** garden-photo analysis, personalized plant selection, understandable recommendations and optional visual previews.
- **B2B — Garden retailers and plant e-commerce websites:** potential integration through GardnAIze APIs and UI components to guide customers toward suitable products and support purchasing decisions.
- **Retail catalog examples:** Truffaut, Leroy Merlin, botanic, Willemse and other garden merchants are possible data-source or distribution examples, **not confirmed partners or authorized commercial data providers**.

Research-stage collection or scraping does not automatically authorize commercial reuse of product descriptions, photos, prices or catalog databases. Commercial ingestion and retailer integration require verification of applicable rights, source terms, provenance and, where needed, permission or a licensing agreement.

## User experience

1. Upload or capture a garden photo and provide location and optional description.
2. Confirm the information and check whether the image is usable.
3. Answer garden-preference questions and provide the relevant consents.
4. Analyze garden characteristics and identify relevant planting zones.
5. Recommend compatible plants with clear explanations.
6. Optionally visualize recommended plants in the garden photo.

## Application modules

| Module | Responsibility |
| --- | --- |
| [GDAI-FRONT](frontend/) | Angular user interface, photo, confirmation, questionnaire and results |
| [GDAI-BACK](backend/) | Spring Boot REST API, asynchronous orchestration, persistence and status tracking |
| [GDAI-VALID](validation/) | FastAPI photo validation with ResNet-18; local segmentation is an intended extension |
| GDAI-VISION | Optional external Gemini Vision garden observations |
| GDAI-PLANT | Horticultural compatibility and Random Forest recommendation engine |
| GDAI-GNERAT | Optional external image generation/editing after recommendations; never blocks E2E |
| [ML data](database/) | PostgreSQL horticultural catalog, provenance and training data |
| [Research](notebooks/) | KNN, K-Means and deep-learning experiments |

## AI and machine learning

| Method | Role | Integration note |
| --- | --- | --- |
| **ResNet-18** | Supervised deep learning to validate garden photos | Service exists; trained weights and end-to-end behavior must be verified |
| **Semantic segmentation** | Detect garden regions useful for planting recommendations | Local model under development; DeepLabV3 is a candidate, not a confirmed deployed model |
| **KNN** | Supervised image-classification experiments | Research notebooks |
| **K-Means** | Unsupervised image clustering | Research notebooks |
| **Random Forest** | Supervised garden-to-plant compatibility ranking | Target recommendation model; training and serving not claimed complete |
| **Gemini Vision** | Optional external image interpretation | Subject to API configuration and consent |
| **Gemini Image** | Optional illustrative photo editing | GDAI-GNERAT, separate from recommendation delivery |

Segmentation outputs should become structured observations (such as zone type and estimated usable area) that can be combined with questionnaire responses and verified horticultural data. A photo alone cannot reliably determine soil properties.

## High-level architecture

```text
GDAI-FRONT (Angular)
       |
       v
GDAI-BACK (Spring Boot) ---> PostgreSQL application data
       |
       +--> GDAI-VALID (ResNet-18 + local segmentation target)
       +--> GDAI-VISION (optional Gemini Vision)
       +--> GDAI-PLANT (Random Forest + horticultural catalog)
       |         |
       |         +--> PostgreSQL ML data
       +--> GDAI-GNERAT (optional Gemini Image, after recommendations)
```

GDAI-FRONT communicates only with GDAI-BACK, not directly with private AI services. The backend coordinates asynchronous processing and exposes its progress to the frontend. Image processing and model training require explicit data permissions.

## Local development

```bash
cp .env.example .env
# Configure local credentials; never commit secrets.
docker compose up --build -d --wait
docker compose ps
```

- Web application: http://localhost:8080
- Backend Swagger UI: http://localhost:8081/swagger-ui.html
- Backend health: http://localhost:8081/actuator/health
- AI-service OpenAPI: http://localhost:8000/docs

See [local deployment](docs/deployment-local.md), [photo workflow](docs/PHOTO_WORKFLOW_PR35.md), and each module README for the actual API contracts and setup instructions. The Compose services and standalone VALID service are not necessarily identical deployments.

## Scope and responsible data use

The MVP focuses on European outdoor gardens. Recommendations depend on climate, exposure, soil, water requirements and user preferences. Botanical sources and photo datasets must be checked for provenance, licenses and reuse permissions. User consent for external vision processing is separate from consent to reuse photos for training.

GardnAIze is an evolving MVP intended to become a commercial B2C/B2B product, not yet a production-certified horticultural advisory service. Models, datasets and optional providers may be unavailable in a local installation.
