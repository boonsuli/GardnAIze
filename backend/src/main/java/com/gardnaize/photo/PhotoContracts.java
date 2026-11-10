package com.gardnaize.photo;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.UUID;

public final class PhotoContracts {
    private PhotoContracts() {}

    @Schema(description = "Stable photo-processing states")
    public record PhotoResponse(UUID id, String status, String message, boolean valid) {}

    public record PhotoStatus(UUID id, String status, String message) {}

    public record VisionResponse(UUID id, String status, String analysisJson) {}

    public record ApiError(String code, String message) {}
}
