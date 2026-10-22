package com.gardnaize.backend.api;

import java.util.List;

public record RecommendationResponse(
        String mode,
        List<PlantSuggestion> plants
) {
    public record PlantSuggestion(String name, String reason) {
    }
}
