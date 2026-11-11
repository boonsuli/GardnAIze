package com.gardnaize.vision;

import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.concurrent.CompletionException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * GDAI-BACK orchestrates a single background task: VISION then PLANT.
 * Existing persisted photo, consent and answers are read through Store.
 * No transaction should remain open during remote calls.
 *
 * Store is an integration seam for the existing PostgreSQL services.
 * Pending jobs are intentionally not resumed after process restart in MVP.
 */
public final class GardenVisionWorkflow {
    private static final Logger log = LoggerFactory.getLogger(GardenVisionWorkflow.class);
    private final Executor executor;
    private final Store store;
    private final Vision vision;
    private final Plant plant;

    public GardenVisionWorkflow(Executor executor, Store store, Vision vision, Plant plant) {
        this.executor = executor;
        this.store = store;
        this.vision = vision;
        this.plant = plant;
    }

    public CompletableFuture<Void> start(UUID analysisId) {
        return CompletableFuture.runAsync(() -> {
            try {
                Input input = store.loadConfirmed(analysisId);
                if (!input.consentConfirmed()) {
                    throw new IllegalStateException("User consent is required");
                }
                store.updateStatus(analysisId, "VISION_RUNNING");
                log.info("GDAI-BACK vision started analysisId={}", analysisId);
                String json = vision.analyze(input);
                store.saveVisionJson(analysisId, json);
                store.updateStatus(analysisId, "PLANT_RUNNING");
                String recommendations = plant.recommend(input, json);
                store.savePlantJson(analysisId, recommendations);
                store.updateStatus(analysisId, "COMPLETED");
                log.info("GDAI-BACK analysis completed analysisId={}", analysisId);
            } catch (Exception ex) {
                log.error("GDAI-BACK analysis failed analysisId={} type={}",
                          analysisId, ex.getClass().getSimpleName());
                store.updateStatus(analysisId, "FAILED");
                throw new CompletionException(ex);
            }
        }, executor);
    }

    public record Input(UUID photoId, byte[] image, String mimeType,
                        String answersJson, boolean consentConfirmed) {}

    public interface Store {
        Input loadConfirmed(UUID analysisId);
        void updateStatus(UUID analysisId, String status);
        void saveVisionJson(UUID analysisId, String json);
        void savePlantJson(UUID analysisId, String json);
    }

    public interface Vision {
        String analyze(Input input);
    }

    public interface Plant {
        String recommend(Input input, String visionJson);
    }
}
