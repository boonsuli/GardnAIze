# GardnAIze Gemini and ML feature contract

## Architecture
Angular photo upload -> Spring Boot /api/v1/gardens/{gardenId}/photos ->
PostgreSQL garden_photos (persisted before external call) -> ai-service POST /analyze ->
Gemini API -> versioned JSON -> garden_photo_analysis -> garden_features.

Gemini API key is **server-side only** (ai-service GEMINI_API_KEY). Never expose it to Angular,
commit it, or use a production photo on the free tier without reviewing terms and consent.

## Three PostgreSQL levels (Flyway V4)
1. **garden_photo_analysis**: one row per provider response/version; raw JSONB and model provenance.
2. **garden_features**: normalized features and source metadata; unknown climate and soil remain NULL.
3. **garden_plant_assessment**: independent labeled garden/plant relevance (0–3), source and assessor.

The existing horticulture.garden_plant_assessment in database/scripts/002 is a separate
standalone schema proposal, **not yet installed by Flyway**. V4 uses the existing application
garden_projects UUID and a temporary scientific-name key until catalog integration.
Do not assume the two assessment tables are synchronized.

## API adapter
Set VISION_ENABLED=true, VISION_BASE_URL=http://ai-service:8000,
VISION_PROVIDER_NAME=gemini-adapter, GEMINI_API_KEY=<secret> on ai-service,
GEMINI_MODEL=gemini-2.5-flash (verify current free-tier availability and quota).
Spring Boot calls POST /analyze with {photoId,mimeType,imageBase64,requirements}.
Response: {schemaVersion,isGarden,isAnalyzable,climateCode:'UNKNOWN',description:{...}}.

Climate cannot be verified from an image. The current backend PR #16 requires a supported
climateCode for acceptance, so a future questionnaire/location confirmation step is needed.
Until then the adapter returns UNKNOWN and the photo is rejected as out of scope, rather
than falsely asserting a climate.

## ML integrity
Store raw response and extracted observations separately. Confirm climate and soil from
independent user/official data. Train Random Forest only with independently reviewed labels,
split by garden to avoid leakage, and keep model outputs separate from labels.
