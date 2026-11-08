# GDAI-FRONT photo confirmation workflow — proposed backend contract

This branch implements the Angular client only. GDAI-BACK endpoints below must be implemented and tested before end-to-end operation.

1. Before upload, Angular checks JPEG/PNG/WebP MIME type and file size <= 1,048,576 bytes. Backend must independently check MIME signatures, supported Gemini Vision formats, content and size. Never trust filename or browser MIME alone.
2. The first **Envoyer** action changes to the preview/confirmation screen locally. No upload occurs yet.
3. **Valider la photo et poursuivre** sends multipart `POST /api/v1/gardens/photos` with `photo` and `description`. Backend persists image to a protected `images-upload/` directory and description to durable storage, then responds `{ "photoId": "uuid", "status": "STORED" }`. Do not log raw image data or description. Log photo ID, outcome, byte count, and correlation ID.
4. Angular calls `POST /api/v1/gardens/photos/{photoId}/validate` asynchronously. GDAI-BACK invokes GDAI-VALID (ResNet-18) and returns `{ "photoId": "uuid", "status": "VALID" | "INVALID" | "PENDING", "message": "..." }`. A PENDING result is polled at 1-second intervals; backend should apply a timeout and return a terminal failure.
5. On INVALID, Angular shows an error in the status bar and returns to the photo form. On VALID, it shows **Photo valide.**, waits 2 seconds, then requests questions.
6. `GET /api/v1/gardens/photos/{photoId}/questions` returns `{ "photoId": "uuid", "questions": [{ "id": "location", "label": "Localisation", "type": "text", "required": true }, { "id": "exposure", "label": "Exposition", "type": "select", "required": true, "options": [{ "value": "FULL_SUN", "label": "Plein soleil" }] }, ...] }`. Return between 5 and 10 questions; types: text, number, boolean, select. Question IDs and option values must match GDAI-PLANT feature mapping.
7. `POST /api/v1/gardens/analyze` accepts `{ "photoId": "uuid", "answers": { "location": "Paris", "exposure": "FULL_SUN" } }`. GDAI-BACK must combine validated image/Gemini features, saved description, questionnaire answers, and plant database attributes for Random Forest inference.

Security: protect uploaded files from public access, use generated server filenames, enforce upload limits and retention policy, and restrict all requests to authorized photo IDs. Persisting invalid images is intentional in this workflow; define cleanup/retention separately.
