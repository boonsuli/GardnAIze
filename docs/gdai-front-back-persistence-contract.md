# GDAI-FRONT → GDAI-BACK — persistence contract v1.1

This change is based directly on `main`, independent of open photo workflow PRs.

## 1. Create garden

`POST /api/v1/gardens` with JSON:

```json
{
    "name": "Mon jardin",
    "location": "Vitry-sur-Seine",
    "countryCode": "FR",
    "climateRegion": "OCEANIC",
    "exposure": "FULL_SUN",
    "soilType": "UNKNOWN"
}
```

`countryCode` and `climateRegion` are optional for older clients (defaults FR/UNKNOWN).
Response includes both fields. `GET /api/v1/gardens/{id}` returns them.

## 2. Preferences

Existing `PUT /api/v1/gardens/{id}/preferences` persists:
`waterAvailability`, `maintenancePreference`, `evergreenPreferred`,
`privacyScreeningRequired`, `desiredHeightCm`.

## 3. Photo

`POST /api/v1/gardens/{gardenId}/photos` multipart/form-data:
- `file`: JPEG or PNG, 1 byte–5 MiB (5 * 1024 * 1024 bytes).
- `description`: optional string up to 1000 characters.

Existing GET `/api/v1/gardens/{gardenId}/photos/{photoId}` is unchanged.
The photo is stored in the **existing** `public.garden_photos.image_bytes` BYTEA
column; description in the new `description` column.

**Important:** the current upload service stores photos *before* external analysis,
including photos later rejected. ResNet-18 validation-before-persistence is a
separate integration task and is **not** implemented by this change.

## Frontend integration still required

The current Angular UI allows WebP, but the existing backend accepts only JPEG/PNG.
Do not claim WebP end-to-end support without adding a tested decoder or conversion.
The current Angular flow also does not upload the selected photo and does not send
`countryCode` or `climateRegion` to `createGarden`. These must be wired in a
separate frontend integration before claiming complete end-to-end persistence.

## Migration / verification

Flyway V11 extends public.garden_projects and public.garden_photos.
Existing photo rows are retained. Historical photos >5 MiB are not deleted.
The old database CHECK permits up to 10 MiB; the service now enforces 5 MiB.

Run `cd backend && mvn test`, verify Flyway V11 against a PostgreSQL 18 instance,
then test multipart 5 MiB boundary, invalid type, description length, and
create/get round-trip. Swagger: `/swagger-ui.html`.

No production upload or database migration was executed by this PR.
