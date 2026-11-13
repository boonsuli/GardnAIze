package com.gardnaize.backend.service;

import com.fasterxml.jackson.databind.JsonNode;
import java.time.Duration;
import java.util.Base64;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.web.client.RestClient;

/** Executes the VALID -> VISION chain, with isolated pools and persisted stage outcomes. */
@Service
public class PhotoWorkflowWorker {
    private static final Logger log = LoggerFactory.getLogger(PhotoWorkflowWorker.class);
    private final JdbcTemplate jdbc;
    private final PhotoWorkflowStateService states;
    private final Executor validPool;
    private final Executor visionPool;
    private final RestClient validClient;
    private final RestClient visionClient;
    private final boolean visionEnabled;
    private final String apiKey;

    public PhotoWorkflowWorker(JdbcTemplate jdbc, PhotoWorkflowStateService states,
            @Qualifier("validationExecutor") Executor validPool,
            @Qualifier("visionExecutor") Executor visionPool,
            @Value("${gardnaize.validation.base-url:http://localhost:9001}") String validUrl,
            @Value("${gardnaize.vision.base-url:http://localhost:9000}") String visionUrl,
            @Value("${gardnaize.vision.enabled:false}") boolean visionEnabled,
            @Value("${gardnaize.vision.api-key:}") String apiKey) {
        this.jdbc = jdbc;
        this.states = states;
        this.validPool = validPool;
        this.visionPool = visionPool;
        this.visionEnabled = visionEnabled;
        this.apiKey = apiKey;
        var factory = new org.springframework.http.client.SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofSeconds(3));
        factory.setReadTimeout(Duration.ofSeconds(30));
        validClient = RestClient.builder().baseUrl(validUrl).requestFactory(factory).build();
        visionClient = RestClient.builder().baseUrl(visionUrl).requestFactory(factory).build();
    }

    public CompletableFuture<Void> execute(UUID requestId, UUID photoId) {
        return CompletableFuture.supplyAsync(() -> validate(requestId, photoId), validPool)
                .thenCompose(valid -> {
                    if (!valid) return CompletableFuture.completedFuture(null);
                    return CompletableFuture.runAsync(() -> analyze(requestId, photoId), visionPool);
                }).exceptionally(error -> {
                    log.error("event=WORKFLOW_FAILED requestId={} photoId={} errorType={}",
                            requestId, photoId, error.getClass().getSimpleName());
                    try {
                        states.photoTransition(photoId, "VISION_FAILED", "WORKFLOW_FAILED");
                        states.requestTransition(requestId, "RUNNING", "FAILED", "WORKFLOW_FAILED", "MODULE_ERROR");
                    } catch (RuntimeException transitionError) {
                        log.error("event=WORKFLOW_STATE_WRITE_FAILED requestId={} errorType={}",
                                requestId, transitionError.getClass().getSimpleName());
                    }
                    return null;
                });
    }

    private boolean validate(UUID requestId, UUID photoId) {
        try (var ignored = MDC.putCloseable("requestId", requestId.toString())) {
            UUID run = states.moduleStarted(requestId, "VALID");
            states.photoTransition(photoId, "VALIDATING", "VALIDATION_STARTED");
            try {
                byte[] bytes = photoBytes(photoId);
                var resource = new ByteArrayResource(bytes) {
                    @Override public String getFilename() { return "garden.webp"; }
                };
                var headers = new HttpHeaders();
                headers.setContentType(MediaType.valueOf("image/webp"));
                var parts = new LinkedMultiValueMap<String, Object>();
                parts.add("photo", new HttpEntity<>(resource, headers));
                @SuppressWarnings("unchecked")
                Map<String, Object> result = validClient.post().uri("/api/v1/validation/photo")
                        .contentType(MediaType.MULTIPART_FORM_DATA).body(parts)
                        .retrieve().body(Map.class);
                if (result == null || !(result.get("valid") instanceof Boolean)) {
                    throw new IllegalStateException("Malformed VALID response");
                }
                boolean accepted = Boolean.TRUE.equals(result.get("valid"));
                states.moduleFinished(requestId, run, "VALID", accepted ? "COMPLETED" : "REJECTED", null);
                states.photoTransition(photoId, accepted ? "VALID" : "NOT_VALID",
                        accepted ? "VALIDATION_COMPLETED" : "VALIDATION_REJECTED");
                if (!accepted) {
                    states.requestTransition(requestId, "RUNNING", "REJECTED", "WORKFLOW_REJECTED", "INVALID_PHOTO");
                }
                return accepted;
            } catch (RuntimeException ex) {
                states.moduleFinished(requestId, run, "VALID", "FAILED", "VALIDATION_ERROR");
                states.photoTransition(photoId, "VALIDATION_FAILED", "VALIDATION_FAILED");
                throw ex;
            }
        }
    }

    private void analyze(UUID requestId, UUID photoId) {
        try (var ignored = MDC.putCloseable("requestId", requestId.toString())) {
            UUID run = states.moduleStarted(requestId, "VISION");
            states.photoTransition(photoId, "VISION_PROCESSING", "VISION_STARTED");
            try {
                if (!visionEnabled) throw new IllegalStateException("Vision disabled");
                byte[] bytes = photoBytes(photoId);
                JsonNode result = visionClient.post().uri("/analyze")
                        .headers(h -> { if (!apiKey.isBlank()) h.setBearerAuth(apiKey); })
                        .contentType(MediaType.APPLICATION_JSON)
                        .body(Map.of("photoId", photoId.toString(), "mimeType", "image/webp",
                                "imageBase64", Base64.getEncoder().encodeToString(bytes)))
                        .retrieve().body(JsonNode.class);
                if (result == null || !result.isObject()
                        || !result.path("isGarden").isBoolean()
                        || !result.path("isAnalyzable").isBoolean()
                        || !result.path("description").isObject()) {
                    throw new IllegalStateException("Malformed VISION response");
                }
                jdbc.update("""
                    UPDATE public.garden_photos SET analysis_provider='external-vision',
                        analysis_json=CAST(? AS jsonb),vision_completed_at=now(),updated_at=now()
                    WHERE id=?
                    """, result.toString(), photoId);
                boolean accepted = result.path("isGarden").asBoolean()
                        && result.path("isAnalyzable").asBoolean();
                states.moduleFinished(requestId, run, "VISION",
                        accepted ? "COMPLETED" : "REJECTED", null);
                states.photoTransition(photoId, accepted ? "VISION_COMPLETED" : "NOT_VALID",
                        accepted ? "VISION_COMPLETED" : "VISION_REJECTED");
                states.requestTransition(requestId, "RUNNING", accepted ? "COMPLETED" : "REJECTED",
                        accepted ? "WORKFLOW_COMPLETED" : "WORKFLOW_REJECTED",
                        accepted ? null : "VISION_NOT_ANALYZABLE");
            } catch (RuntimeException ex) {
                states.moduleFinished(requestId, run, "VISION", "FAILED", "VISION_ERROR");
                throw ex;
            }
        }
    }

    private byte[] photoBytes(UUID photoId) {
        byte[] bytes = jdbc.queryForObject(
                "SELECT image_bytes FROM public.garden_photos WHERE id=?", byte[].class, photoId);
        if (bytes == null || bytes.length == 0) throw new IllegalStateException("Photo not found");
        return bytes;
    }
}
