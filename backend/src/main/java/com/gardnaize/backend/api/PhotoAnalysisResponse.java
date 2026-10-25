package com.gardnaize.backend.api;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.UUID;

public record PhotoAnalysisResponse(
        UUID photoId,
        UUID gardenId,
        String photoStatus,
        String processingStatus,
        String rejectionReason,
        JsonNode analysis
) {
}
