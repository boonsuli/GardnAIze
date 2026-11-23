package com.gardnaize.backend.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

/** Executes PLANT after user submission; no VISION replay. */
@Service
public class PlantRecommendationWorker {
    private static final Logger log = LoggerFactory.getLogger(PlantRecommendationWorker.class);
    private final JdbcTemplate jdbc;
    private final PhotoWorkflowFencingService fenced;
    private final Executor pool;
    private final RestClient client;
    private final ObjectMapper mapper;

    public PlantRecommendationWorker(JdbcTemplate jdbc, PhotoWorkflowFencingService fenced,
            @Qualifier("visionExecutor") Executor pool, ObjectMapper mapper,
            @Value("${gardnaize.plant.base-url:http://localhost:8000}") String baseUrl) {
        this.jdbc=jdbc; this.fenced=fenced; this.pool=pool; this.mapper=mapper;
        var factory=new org.springframework.http.client.SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofSeconds(3));
        factory.setReadTimeout(Duration.ofSeconds(60));
        this.client=RestClient.builder().baseUrl(baseUrl).requestFactory(factory).build();
    }

    public CompletableFuture<Void> execute(UUID requestId, UUID photoId,
            PhotoWorkflowFencingService.Lease lease) {
        return CompletableFuture.runAsync(() -> run(requestId, photoId, lease), pool);
    }

    private void run(UUID requestId, UUID photoId, PhotoWorkflowFencingService.Lease lease) {
        UUID runId = null;
        try {
            runId = fenced.moduleStarted(lease, "PLANT");
            fenced.photoTransition(lease, photoId, "PLANT_PROCESSING", "PLANT_STARTED");
            var input = jdbc.queryForMap("""
                SELECT q.answers::text AS answers, p.analysis_json::text AS vision
                FROM public.garden_photo_requests r
                JOIN public.garden_photo_questionnaire q ON q.photo_id=r.photo_id
                JOIN public.garden_photos p ON p.id=r.photo_id
                WHERE r.request_id=? AND q.answers_submitted_at IS NOT NULL
                  AND p.vision_completed_at IS NOT NULL
                """, requestId);
            JsonNode answers = mapper.readTree((String) input.get("answers"));
            JsonNode vision = mapper.readTree((String) input.get("vision"));
            Map<String,Object> payload = new LinkedHashMap<>();
            payload.put("request_id", requestId.toString());
            payload.put("garden", gardenProfile(answers, vision));
            payload.put("limit", 10);
            JsonNode result = client.post().uri("/v1/recommendations")
                    .contentType(MediaType.APPLICATION_JSON).body(payload)
                    .retrieve().body(JsonNode.class);
            if (result == null || !"COMPLETED".equals(result.path("status").asText())
                    || !result.path("request_id").asText().equals(requestId.toString())
                    || !result.path("recommendations").isArray()
                    || result.path("recommendations").isEmpty()
                    || result.path("recommendations").size() > 10) {
                throw new IllegalStateException("PLANT did not return usable recommendations");
            }
            // Store before terminal transition. Fenced DB writes reject stale workers.
            fenced.saveRecommendations(lease, result.path("recommendations").toString(),
                    result.path("model_version").asText(null),
                    result.path("recommendations").get(0).path("method").asText(null));
            fenced.moduleFinished(lease, runId, "PLANT", "COMPLETED", null);
            fenced.photoTransition(lease, photoId, "COMPLETED", "RECOMMENDATIONS_READY");
            fenced.requestTransition(lease, "COMPLETED", "WORKFLOW_COMPLETED", null);
        } catch (PhotoWorkflowFencingService.LeaseLostException ex) {
            log.warn("event=STALE_PLANT_WORKER_DISCARDED requestId={}", requestId);
        } catch (Exception ex) {
            log.error("event=PLANT_FAILED requestId={} errorType={}", requestId, ex.getClass().getSimpleName());
            try {
                if (runId != null) fenced.moduleFinished(lease, runId, "PLANT", "FAILED", "PLANT_ERROR");
                fenced.requestTransition(lease, "FAILED", "PLANT_FAILED", "PLANT_ERROR");
            } catch (RuntimeException stale) {
                log.warn("event=PLANT_FAILURE_REQUIRES_RECONCILIATION requestId={}", requestId);
            }
        }
    }

    private Map<String,Object> gardenProfile(JsonNode answers, JsonNode vision) {
        Map<String,Object> profile=new LinkedHashMap<>();
        String exposure=answers.path("exposure").asText("");
        String water=answers.path("waterAvailability").asText("");
        if (!exposure.isBlank()) profile.put("sun_exposure", exposure);
        if (!water.isBlank()) profile.put("water_availability", water);
        // No inferred temperature, soil, or plant characteristics from image alone.
        if (answers.path("evergreenPreferred").isBoolean())
            profile.put("evergreen_preferred", answers.path("evergreenPreferred").asBoolean());
        if (answers.path("privacyScreeningRequired").isBoolean())
            profile.put("privacy_screening_required", answers.path("privacyScreeningRequired").asBoolean());
        return profile;
    }
}
