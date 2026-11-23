package com.gardnaize.backend.service;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.List;
import java.util.Optional;
import org.springframework.stereotype.Component;

/**
 * Deterministic selection of at most one optional context question.
 * Only known questionnaire keys are returned; FRONT owns translations.
 */
@Component
public class GardenContextQuestionSelector {
    public record Question(String key, String reason) {}

    public Optional<Question> select(JsonNode vision, JsonNode answers) {
        if (vision == null || !vision.path("isGarden").asBoolean(false)
                || !vision.path("isAnalyzable").asBoolean(false)) {
            return Optional.empty();
        }
        JsonNode description = vision.path("description");
        JsonNode features = description.path("features");
        if (features.path("fence").asBoolean(false) &&
                !answered(answers, "privacy")) {
            return Optional.of(new Question("privacy", "FENCE_DETECTED"));
        }
        if (features.path("slope").asBoolean(false) &&
                !answered(answers, "rootDevelopment")) {
            return Optional.of(new Question("rootDevelopment", "SLOPE_DETECTED"));
        }
        if (features.path("terrace").asBoolean(false) &&
                !answered(answers, "aerialVolume")) {
            return Optional.of(new Question("aerialVolume", "TERRACE_DETECTED"));
        }
        return Optional.empty();
    }

    private boolean answered(JsonNode answers, String key) {
        JsonNode answer = answers == null ? null : answers.get(key);
        return answer != null && !answer.isNull() &&
                (!answer.isTextual() || !answer.asText().isBlank());
    }
}
