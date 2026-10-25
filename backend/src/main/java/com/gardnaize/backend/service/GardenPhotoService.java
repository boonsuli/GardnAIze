package com.gardnaize.backend.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.gardnaize.backend.api.PhotoAnalysisResponse;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.time.Duration;
import java.util.Base64;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import javax.imageio.ImageIO;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

@Service
public class GardenPhotoService {
    private static final long MAX_BYTES = 10L * 1024 * 1024;
    private static final Set<String> ACCEPTED_CLIMATES = Set.of("TEMPERATE_CONTINENTAL");
    private final JdbcTemplate jdbc;
    private final ObjectMapper mapper;
    private final RestClient providerClient;
    private final String providerName;
    private final String apiKey;
    private final boolean enabled;

    public GardenPhotoService(JdbcTemplate jdbc, ObjectMapper mapper,
            @Value("${gardnaize.vision.base-url:http://localhost:9000}") String baseUrl,
            @Value("${gardnaize.vision.provider-name:external-vision}") String providerName,
            @Value("${gardnaize.vision.api-key:}") String apiKey,
            @Value("${gardnaize.vision.enabled:false}") boolean enabled) {
        this.jdbc = jdbc;
        this.mapper = mapper;
        this.providerName = providerName;
        this.apiKey = apiKey;
        this.enabled = enabled;
        var factory = new org.springframework.http.client.SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofSeconds(3));
        factory.setReadTimeout(Duration.ofSeconds(30));
        this.providerClient = RestClient.builder().baseUrl(baseUrl).requestFactory(factory).build();
    }

    public PhotoAnalysisResponse upload(UUID gardenId, MultipartFile file) {
        if (!Boolean.TRUE.equals(jdbc.queryForObject(
                "SELECT EXISTS(SELECT 1 FROM garden_projects WHERE id = ?)", Boolean.class, gardenId))) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Garden not found");
        }
        if (file == null || file.isEmpty() || file.getSize() > MAX_BYTES) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Photo must be 1–10 MB");
        }
        String type = file.getContentType();
        if (!Set.of("image/jpeg", "image/png").contains(type)) {
            throw new ResponseStatusException(HttpStatus.UNSUPPORTED_MEDIA_TYPE,
                    "Only JPEG and PNG are supported by the backend MVP");
        }
        byte[] bytes;
        try {
            bytes = file.getBytes();
        } catch (IOException ex) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Cannot read photo");
        }
        if (bytes.length > MAX_BYTES) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Photo too large");
        }
        BufferedImage image;
        try {
            image = ImageIO.read(new ByteArrayInputStream(bytes));
        } catch (IOException ex) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Invalid image");
        }
        if (image == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Unsupported image");
        }
        UUID photoId = UUID.randomUUID();
        String filename = file.getOriginalFilename() == null ? "photo" : file.getOriginalFilename();
        filename = filename.replaceAll("[^a-zA-Z0-9._-]", "_");
        if (filename.length() > 255) {
            filename = filename.substring(0, 255);
        }
        jdbc.update("""
            INSERT INTO garden_photos (id,garden_id,original_filename,content_type,file_size_bytes,
                width_px,height_px,image_bytes,photo_status,processing_status)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            """, photoId, gardenId, filename, type, bytes.length,
                image.getWidth(), image.getHeight(), bytes, "RECEIVED", "INITIALIZED");
        transition(photoId, "RECEIVED", "INITIALIZED", "Photo persisted on upload");

        if (image.getWidth() < 640 || image.getHeight() < 480) {
            // Minimum resolution is enforced by DB constraint, so this branch is unreachable.
            return reject(photoId, gardenId, "INSUFFICIENT_RESOLUTION");
        }
        transition(photoId, "CHECKED", "IN_PROGRESS", "Local validation passed");
        if (!enabled) {
            transition(photoId, "TRANSFER_FAILED", "FAILED", "Vision provider is not configured");
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,
                    "Vision provider is disabled; photo remains persisted");
        }
        try {
            // Provider-neutral adapter contract; configure an external adapter at base-url.
            JsonNode result = providerClient.post().uri("/analyze")
                    .headers(headers -> {
                        if (!apiKey.isBlank()) {
                            headers.setBearerAuth(apiKey);
                        }
                    })
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(Map.of("photoId", photoId.toString(), "mimeType", type,
                            "imageBase64", Base64.getEncoder().encodeToString(bytes),
                            "requirements", Map.of("gardenRequired", true,
                                    "allowedClimateCodes", ACCEPTED_CLIMATES,
                                    "minimumWidthPx", 640, "minimumHeightPx", 480)))
                    .retrieve().body(JsonNode.class);
            transition(photoId, "TRANSFERRED", "IN_PROGRESS", "External provider responded");
            if (result == null || !result.isObject()
                    || !result.has("isGarden") || !result.get("isGarden").isBoolean()
                    || !result.has("isAnalyzable") || !result.get("isAnalyzable").isBoolean()
                    || !result.hasNonNull("climateCode") || !result.get("climateCode").isTextual()
                    || !result.has("description") || !result.get("description").isObject()) {
                return reject(photoId, gardenId, "INVALID_PROVIDER_RESPONSE");
            }
            String rawJson = mapper.writeValueAsString(result);
            jdbc.update("UPDATE garden_photos SET analysis_provider=?, analysis_json=CAST(? AS jsonb), updated_at=now() WHERE id=?",
                    providerName, rawJson, photoId);
            // Preserve immutable provider evidence separately from normalized ML features.
            UUID analysisId = UUID.randomUUID();
            jdbc.update("""
                INSERT INTO garden_photo_analysis
                  (id,photo_id,provider_name,model_name,schema_version,analysis_status,raw_response)
                VALUES (?,?,?,?,?,'SUCCEEDED',CAST(? AS jsonb))
                """, analysisId, photoId, providerName, "gemini-adapter",
                    result.path("schemaVersion").asText("1.0"), rawJson);
            JsonNode description = result.path("description");
            jdbc.update("""
                INSERT INTO garden_features
                  (id,garden_id,source_photo_analysis_id,schema_version,space_type,shade_level,
                   privacy_exposure,plantable_areas_detected,visible_surfaces,visible_vegetation,
                   feature_provenance)
                VALUES (?,?,?,?,?,?,?,?,
                        CAST(? AS jsonb),CAST(? AS jsonb),CAST(? AS jsonb))
                """, UUID.randomUUID(), gardenId, analysisId,
                    result.path("schemaVersion").asText("1.0"),
                    nullableText(description.path("spaceType")),
                    nullableText(description.path("shadeLevel")),
                    nullableText(description.path("privacyExposure")),
                    description.path("plantableAreasDetected").isBoolean()
                        ? description.path("plantableAreasDetected").asBoolean() : null,
                    mapper.writeValueAsString(description.path("surfaces").isArray()
                        ? description.path("surfaces") : mapper.createArrayNode()),
                    mapper.writeValueAsString(description.path("visibleVegetation").isArray()
                        ? description.path("visibleVegetation") : mapper.createArrayNode()),
                    mapper.writeValueAsString(Map.of("source", "GEMINI_IMAGE_OBSERVATION", "climateVerified", false, "soilVerified", false)));
            transition(photoId, "ANALYZED", "IN_PROGRESS", "Provider JSON persisted");
            if (!result.path("isGarden").asBoolean() || !result.path("isAnalyzable").asBoolean()) {
                return reject(photoId, gardenId, "NOT_ANALYZABLE_GARDEN");
            }
            if (!ACCEPTED_CLIMATES.contains(result.path("climateCode").asText())) {
                return reject(photoId, gardenId, "CLIMATE_UNVERIFIED_OR_OUT_OF_SCOPE");
            }
            transition(photoId, "ACCEPTED", "COMPLETED", "MVP requirements met");
            return get(photoId, gardenId);
        } catch (RestClientException | com.fasterxml.jackson.core.JsonProcessingException ex) {
            transition(photoId, "TRANSFER_FAILED", "FAILED", "Provider request or response failed");
            throw new ResponseStatusException(HttpStatus.BAD_GATEWAY,
                    "External photo analysis failed; uploaded photo remains persisted");
        }
    }

    private static String nullableText(JsonNode node) {
        return node.isTextual() && !node.asText().isBlank() ? node.asText() : null;
    }

    private PhotoAnalysisResponse reject(UUID photoId, UUID gardenId, String reason) {
        jdbc.update("UPDATE garden_photos SET rejection_reason=?, updated_at=now() WHERE id=?", reason, photoId);
        transition(photoId, "REJECTED", "COMPLETED", reason);
        return get(photoId, gardenId);
    }

    private void transition(UUID photoId, String photoStatus, String processingStatus, String details) {
        jdbc.update("UPDATE garden_photos SET photo_status=?, processing_status=?, updated_at=now() WHERE id=?",
                photoStatus, processingStatus, photoId);
        jdbc.update("INSERT INTO garden_photo_status_history (photo_id,photo_status,processing_status,details) VALUES (?,?,?,?)",
                photoId, photoStatus, processingStatus, details);
    }

    public PhotoAnalysisResponse get(UUID photoId, UUID gardenId) {
        var rows = jdbc.query("""
                SELECT photo_status,processing_status,rejection_reason,analysis_json::text
                FROM garden_photos WHERE id=? AND garden_id=?
                """, (rs, n) -> {
                    JsonNode analysis = null;
                    try {
                        if (rs.getString(4) != null) {
                            analysis = mapper.readTree(rs.getString(4));
                        }
                    } catch (IOException ex) {
                        throw new IllegalStateException("Corrupt persisted analysis JSON", ex);
                    }
                    return new PhotoAnalysisResponse(photoId, gardenId, rs.getString(1),
                            rs.getString(2), rs.getString(3), analysis);
                }, photoId, gardenId);
        if (rows.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Photo not found");
        }
        return rows.getFirst();
    }
}
