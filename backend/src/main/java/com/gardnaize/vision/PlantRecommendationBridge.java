package com.gardnaize.vision;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Map;
import org.springframework.web.client.RestClient;

/**
 * MVP bridge to existing /recommendations demo-rules endpoint.
 * Future Random Forest adapter can replace this implementation.
 * Vision observations are preserved separately; the current demo
 * recommender only accepts location, exposure and soilType.
 */
public final class PlantRecommendationBridge implements GardenVisionWorkflow.Plant {
    private final RestClient client;
    private final ObjectMapper mapper;

    public PlantRecommendationBridge(RestClient client, ObjectMapper mapper) {
        this.client = client;
        this.mapper = mapper;
    }

    @Override
    public String recommend(GardenVisionWorkflow.Input input, String visionJson) {
        try {
            JsonNode vision = mapper.readTree(visionJson);
            if (!vision.path("isGarden").asBoolean(false)
                    || !vision.path("isUsable").asBoolean(false)) {
                throw new IllegalArgumentException("Vision result is not a usable garden");
            }
            JsonNode answers = mapper.readTree(input.answersJson());
            String location = requiredText(answers, "location");
            String exposure = requiredText(answers, "exposure");
            String soilType = requiredText(answers, "soilType");
            String response = client.post().uri("/recommendations")
                    .body(Map.of("location", location, "exposure", exposure, "soilType", soilType))
                    .retrieve().body(String.class);
            if (response == null || response.isBlank()) {
                throw new IllegalStateException("GDAI-PLANT returned an empty response");
            }
            return response;
        } catch (JsonProcessingException ex) {
            throw new IllegalArgumentException("Invalid stored JSON", ex);
        }
    }

    private static String requiredText(JsonNode answers, String key) {
        String value = answers.path(key).asText("");
        if (value.isBlank()) {
            throw new IllegalArgumentException("Missing questionnaire field: " + key);
        }
        return value;
    }
}
