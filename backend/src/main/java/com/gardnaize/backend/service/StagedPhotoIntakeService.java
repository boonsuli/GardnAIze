package com.gardnaize.backend.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.gardnaize.backend.api.PhotoProcessingRequestResponse;
import java.time.OffsetDateTime;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

/**
 * Staged intake, additive to PR35 legacy upload:
 * accept mandatory external consent and queue VALID/VISION before the
 * user finishes the questionnaire. Training consent is independent.
 */
@Service
public class StagedPhotoIntakeService {
    private static final String EXTERNAL_CONSENT = "privacy.externalProcessingNotice";
    private final GardenPhotoService photos;
    private final JdbcTemplate jdbc;
    private final ObjectMapper mapper;

    public StagedPhotoIntakeService(GardenPhotoService photos, JdbcTemplate jdbc, ObjectMapper mapper) {
        this.photos = photos;
        this.jdbc = jdbc;
        this.mapper = mapper;
    }

    @Transactional
    public PhotoProcessingRequestResponse start(UUID gardenId, MultipartFile file,
            String description, String consentKey, boolean trainingConsent) {
        if (!EXTERNAL_CONSENT.equals(consentKey)) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN,
                    "External image processing consent is required");
        }
        // No external request occurs during this transaction. The master claims
        // the request only after the consent row and request have committed.
        var persisted = photos.upload(gardenId, file, description);
        UUID photoId = persisted.photoId();
        UUID requestId = UUID.randomUUID();
        jdbc.update("""
            INSERT INTO public.garden_photo_questionnaire
              (photo_id,answers,consent_key,consented_at,training_consent)
            VALUES (?, '{}'::jsonb, ?, now(), ?)
            """, photoId, consentKey, trainingConsent);
        jdbc.update("""
            INSERT INTO public.garden_photo_requests
              (request_id,garden_id,photo_id,status,intake_mode)
            VALUES (?,?,?,'ACCEPTED','STAGED')
            """, requestId, gardenId, photoId);
        jdbc.update("""
            INSERT INTO public.garden_photo_request_history(request_id,status,event_code)
            VALUES (?,'ACCEPTED','STAGED_REQUEST_RECORDED')
            """, requestId);
        return new PhotoProcessingRequestResponse(requestId, gardenId, photoId, "ACCEPTED",
                OffsetDateTime.now(),
                "/api/v1/gardens/" + gardenId + "/photo-requests/" + requestId);
    }

    @Transactional
    public void submitAnswers(UUID gardenId, UUID requestId, JsonNode answers) {
        if (answers == null || !answers.isObject()
                || !present(answers, "exposure")
                || !present(answers, "waterAvailability")
                || !present(answers, "maintenancePreference")) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
                    "Required questionnaire answers missing");
        }
        String json;
        try {
            json = mapper.writeValueAsString(answers);
        } catch (com.fasterxml.jackson.core.JsonProcessingException ex) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Invalid answers");
        }
        // The questionnaire is immutable after its first final submission.
        int updated = jdbc.update("""
            UPDATE public.garden_photo_questionnaire q
            SET answers=CAST(? AS jsonb),answers_submitted_at=now()
            WHERE q.answers_submitted_at IS NULL
              AND EXISTS (
                SELECT 1 FROM public.garden_photo_requests r
                WHERE r.photo_id=q.photo_id AND r.garden_id=?
                  AND r.request_id=? AND r.intake_mode='STAGED'
                  AND r.status NOT IN ('FAILED','REJECTED','RECONCILIATION_REQUIRED'))
            """, json, gardenId, requestId);
        if (updated != 1) {
            throw new ResponseStatusException(HttpStatus.CONFLICT,
                    "Request unavailable or questionnaire already submitted");
        }
        // If VISION already finished, release the durable wait for the PLANT master.
        int ready = jdbc.update("""
            UPDATE public.garden_photo_requests
            SET status='READY_FOR_PLANT', updated_at=now()
            WHERE garden_id=? AND request_id=? AND status='WAITING_ANSWERS'
            """, gardenId, requestId);
        if (ready == 1) {
            jdbc.update("""
                INSERT INTO public.garden_photo_request_history
                  (request_id,previous_status,status,event_code)
                VALUES (?,'WAITING_ANSWERS','READY_FOR_PLANT','PLANT_READY')
                """, requestId);
        }
        jdbc.update("""
            INSERT INTO public.garden_photo_request_history(request_id,status,event_code)
            SELECT request_id,status,'QUESTIONNAIRE_SUBMITTED'
            FROM public.garden_photo_requests WHERE garden_id=? AND request_id=?
            """, gardenId, requestId);
    }

    private boolean present(JsonNode answers, String key) {
        JsonNode value = answers.get(key);
        return value != null && !value.isNull()
                && (!value.isTextual() || !value.asText().isBlank());
    }
}
