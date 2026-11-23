package com.gardnaize.backend.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Duration;
import java.time.Instant;
import org.junit.jupiter.api.Test;

class VisionPlantOrchestrationTest {
    private final ObjectMapper mapper = new ObjectMapper();

    @Test
    void contextQuestionSelectsFenceAndAvoidsAnsweredProperty() throws Exception {
        var selector = new GardenContextQuestionSelector();
        var vision = mapper.readTree("""
            {"isGarden":true,"isAnalyzable":true,"description":{"features":{
              "fence":true,"slope":true,"terrace":true}}}
            """);
        assertEquals("privacyScreeningRequired", selector.select(vision, mapper.readTree("{}")).orElseThrow().key());
        assertEquals("rootSpace", selector.select(vision,
                mapper.readTree("{\"privacyScreeningRequired\":\"YES\"}")).orElseThrow().key());
        assertTrue(selector.select(vision, mapper.readTree("""
            {"privacyScreeningRequired":"YES","rootSpace":"LOW","matureSpread":"SMALL"}
            """)).isEmpty());
    }

    @Test
    void unusableVisionNeverProducesQuestion() throws Exception {
        var selector = new GardenContextQuestionSelector();
        assertTrue(selector.select(mapper.readTree("""
            {"isGarden":false,"isAnalyzable":true,"description":{"features":{"fence":true}}}
            """), mapper.createObjectNode()).isEmpty());
    }

    @Test
    void joinGateDoesNotSkipMandatoryInputs() {
        var gate = new VisionPlantWorkflowWorker();
        Instant now = Instant.parse("2026-11-23T12:00:00Z");
        Instant deadline = gate.contextDeadline(now.minusSeconds(120), Duration.ofSeconds(60));
        assertEquals(VisionPlantWorkflowWorker.Decision.WAIT_FOR_VISION,
                gate.evaluate(false, false, true, true, false, deadline, now));
        assertEquals(VisionPlantWorkflowWorker.Decision.VISION_UNAVAILABLE,
                gate.evaluate(true, false, true, true, false, deadline, now));
        assertEquals(VisionPlantWorkflowWorker.Decision.WAIT_FOR_QUESTIONNAIRE,
                gate.evaluate(true, true, false, true, false, deadline, now));
        assertEquals(VisionPlantWorkflowWorker.Decision.READY_FOR_PLANT,
                gate.evaluate(true, true, true, true, false, deadline, now));
        assertEquals(VisionPlantWorkflowWorker.Decision.WAIT_FOR_CONTEXT_QUESTION,
                gate.evaluate(true, true, true, true, false, now.plusSeconds(60), now));
    }
}
