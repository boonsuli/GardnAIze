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
    private final PhotoWorkflowFencingService fenced;
    private final Executor validPool;
    private final Executor visionPool;
    private final RestClient validClient;
    private final RestClient visionClient;
    private final boolean visionEnabled;
    private final String apiKey;

    public PhotoWorkflowWorker(JdbcTemplate jdbc, PhotoWorkflowStateService states,
            PhotoWorkflowFencingService fenced,
            @Qualifier("validationExecutor") Executor validPool,
            @Qualifier("visionExecutor") Executor visionPool,
            @Value("${gardnaize.validation.base-url:http://localhost:9001}") String validUrl,
            @Value("${gardnaize.vision.base-url:http://localhost:9000}") String visionUrl,
            @Value("${gardnaize.vision.enabled:false}") boolean visionEnabled,
            @Value("${gardnaize.vision.api-key:}") String apiKey) {
        this.jdbc = jdbc;
        this.states = states;
        this.fenced = fenced;
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
        var lease = jdbc.queryForObject("""
            SELECT lease_owner,lease_generation FROM public.garden_photo_requests
            WHERE request_id=? AND status='RUNNING' AND lease_until > now()
            """, (rs, row) -> new PhotoWorkflowFencingService.Lease(requestId,
                    rs.getString(1), rs.getLong(2)), requestId);
        return execute(requestId, photoId, lease);
    }

    public CompletableFuture<Void> execute(UUID requestId, UUID photoId,
            PhotoWorkflowFencingService.Lease lease) {
        java.util.concurrent.atomic.AtomicReference<String> stage = new java.util.concurrent.atomic.AtomicReference<>("VALID");
        return CompletableFuture.supplyAsync(() -> validate(requestId, photoId, lease), validPool)
                .thenCompose(valid -> {
                    if (!valid) return CompletableFuture.completedFuture(null);
                    stage.set("VISION");
                    return CompletableFuture.runAsync(() -> analyze(requestId, photoId, lease), visionPool);
                }).exceptionally(error -> {
                    log.error("event=WORKFLOW_FAILED requestId={} photoId={} errorType={}",
                            requestId, photoId, error.getClass().getSimpleName());
                    try {
                        if (error.getCause() instanceof PhotoWorkflowFencingService.LeaseLostException
                                || error instanceof PhotoWorkflowFencingService.LeaseLostException) {
                            log.warn("event=STALE_WORKER_DISCARDED requestId={}", requestId);
                            return null;
                        }
                        if ("VISION".equals(stage.get())) {
                            fenced.photoTransition(lease, photoId, "VISION_FAILED", "WORKFLOW_FAILED");
                        } else {
                            fenced.photoTransition(lease, photoId, "VALIDATION_FAILED", "WORKFLOW_FAILED");
                        }
                        fenced.requestTransition(lease, "FAILED", "WORKFLOW_FAILED", "MODULE_ERROR");
                    } catch (RuntimeException transitionError) {
                        log.error("event=WORKFLOW_STATE_WRITE_FAILED requestId={} errorType={}",
                                requestId, transitionError.getClass().getSimpleName());
                    }
                    return null;
                });
    }

    private boolean validate(UUID requestId, UUID photoId, PhotoWorkflowFencingService.Lease lease) {
        try (var ignored = MDC.putCloseable("requestId", requestId.toString())) {
            UUID run = fenced.moduleStarted(lease, "VALID");
            fenced.photoTransition(lease, photoId, "VALIDATING", "VALIDATION_STARTED");
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
                if (result == null || !(result.get("valid") instanceof Boolean)
                        || !(result.get("status") instanceof String)
                        || !(result.get("confidence") instanceof Number)) {
                    throw new IllegalStateException("Malformed VALID response");
                }
                boolean accepted = Boolean.TRUE.equals(result.get("valid"));
                fenced.moduleFinished(lease, run, "VALID", accepted ? "COMPLETED" : "REJECTED", null);
                fenced.photoTransition(lease, photoId, accepted ? "VALID" : "NOT_VALID",
                        accepted ? "VALIDATION_COMPLETED" : "VALIDATION_REJECTED");
                if (accepted) {
                    fenced.photoTransition(lease, photoId, "VISION_PENDING", "VISION_QUEUED");
                }
                if (!accepted) {
                    fenced.requestTransition(lease, "REJECTED", "WORKFLOW_REJECTED", "INVALID_PHOTO");
                }
                return accepted;
            } catch (PhotoWorkflowFencingService.LeaseLostException ex) {
                throw ex;
            } catch (RuntimeException ex) {
                fenced.moduleFinished(lease, run, "VALID", "FAILED", "VALIDATION_ERROR");
                fenced.photoTransition(lease, photoId, "VALIDATION_FAILED", "VALIDATION_FAILED");
                throw ex;
            }
        }
    }

    private void analyze(UUID requestId, UUID photoId, PhotoWorkflowFencingService.Lease lease) {
        try (var ignored = MDC.putCloseable("requestId", requestId.toString())) {
            UUID run = fenced.moduleStarted(lease, "VISION");
            fenced.photoTransition(lease, photoId, "VISION_PROCESSING", "VISION_STARTED");
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
                fenced.saveVision(lease, photoId, result.toString());
                boolean accepted = result.path("isGarden").asBoolean()
                        && result.path("isAnalyzable").asBoolean();
                fenced.moduleFinished(lease, run, "VISION",
                        accepted ? "COMPLETED" : "REJECTED", null);
                fenced.photoTransition(lease, photoId, accepted ? "VISION_COMPLETED" : "NOT_VALID",
                        accepted ? "VISION_COMPLETED" : "VISION_REJECTED");
                fenced.requestTransition(lease, accepted ? "COMPLETED" : "REJECTED",
                        accepted ? "WORKFLOW_COMPLETED" : "WORKFLOW_REJECTED",
                        accepted ? null : "VISION_NOT_ANALYZABLE");
            } catch (PhotoWorkflowFencingService.LeaseLostException ex) {
                throw ex;
            } catch (RuntimeException ex) {
                fenced.moduleFinished(lease, run, "VISION", "FAILED", "VISION_ERROR");
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
