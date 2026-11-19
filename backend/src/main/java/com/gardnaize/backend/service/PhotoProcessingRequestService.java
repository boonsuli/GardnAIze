package com.gardnaize.backend.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.gardnaize.backend.api.PhotoAnalysisResponse;
import com.gardnaize.backend.api.PhotoProcessingRequestResponse;
import java.time.OffsetDateTime;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

/** Records an accepted request atomically; external dispatch is a separate workflow stage. */
@Service
public class PhotoProcessingRequestService {
    private static final Logger log = LoggerFactory.getLogger(PhotoProcessingRequestService.class);
    private static final String CONSENT_KEY = "privacy.externalProcessingNotice";
    private final GardenPhotoService photos;
    private final JdbcTemplate jdbc;
    private final ObjectMapper mapper;

    public PhotoProcessingRequestService(GardenPhotoService photos, JdbcTemplate jdbc, ObjectMapper mapper) {
        this.photos = photos;
        this.jdbc = jdbc;
        this.mapper = mapper;
    }

    @Transactional
    public PhotoProcessingRequestResponse accept(UUID gardenId, MultipartFile file, String description,
                                                   String answersJson, String consentKey) {
        if (!CONSENT_KEY.equals(consentKey)) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Explicit external processing consent required");
        }
        JsonNode answers;
        try {
            answers = mapper.readTree(answersJson == null ? "" : answersJson);
        } catch (JsonProcessingException ex) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Invalid questionnaire JSON");
        }
        if (!answers.isObject() || !answers.hasNonNull("exposure")
                || !answers.hasNonNull("waterAvailability")
                || !answers.hasNonNull("maintenancePreference")) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Required questionnaire answers missing");
        }

        // This overload persists the photo without contacting the external vision provider.
        PhotoAnalysisResponse persisted = photos.upload(gardenId, file, description);
        UUID requestId = UUID.randomUUID();
        UUID photoId = persisted.photoId();
        jdbc.update("""
            INSERT INTO public.garden_photo_questionnaire (photo_id, answers, consent_key, consented_at)
            VALUES (?, CAST(? AS jsonb), ?, now())
            """, photoId, answersJson, consentKey);
        jdbc.update("""
            INSERT INTO public.garden_photo_requests (request_id, garden_id, photo_id, status)
            VALUES (?, ?, ?, 'ACCEPTED')
            """, requestId, gardenId, photoId);
        jdbc.update("""
            INSERT INTO public.garden_photo_request_history (request_id, status, event_code)
            VALUES (?, 'ACCEPTED', 'REQUEST_RECORDED')
            """, requestId);
        log.info("photo_request.accepted requestId={} gardenId={} photoId={} status=ACCEPTED",
                requestId, gardenId, photoId);
        return new PhotoProcessingRequestResponse(requestId, gardenId, photoId, "ACCEPTED",
                OffsetDateTime.now(), statusUrl(gardenId, requestId));
    }

    public PhotoProcessingRequestResponse get(UUID gardenId, UUID requestId) {
        var rows = jdbc.query("""
            SELECT photo_id, status, created_at
            FROM public.garden_photo_requests
            WHERE garden_id=? AND request_id=?
            """, (rs, row) -> new PhotoProcessingRequestResponse(
                    requestId, gardenId, (UUID) rs.getObject("photo_id"),
                    rs.getString("status"),
                    rs.getObject("created_at", OffsetDateTime.class),
                    statusUrl(gardenId, requestId)), gardenId, requestId);
        if (rows.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Processing request not found");
        }
        return rows.getFirst();
    }

    private static String statusUrl(UUID gardenId, UUID requestId) {
        return "/api/v1/gardens/" + gardenId + "/photo-requests/" + requestId;
    }
}
