package com.gardnaize.vision;

import java.io.IOException;
import java.util.Map;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClient;
import org.springframework.web.multipart.MultipartFile;

/**
 * GDAI-BACK public entry point. Validation is delegated to GDAI-VALID.
 * The confirmation endpoint is intentionally not exposed until durable,
 * expiring temporary photo storage and explicit user consent are implemented.
 */
@RestController
@RequestMapping("/api/v1/vision")
public class VisionValidationController {
    private static final Logger log = LoggerFactory.getLogger(VisionValidationController.class);
    private final RestClient validClient;

    public VisionValidationController(
            @Value("${gardnaize.ai.base-url:http://localhost:8000}") String validBaseUrl) {
        this.validClient = RestClient.builder().baseUrl(validBaseUrl).build();
    }

    @PostMapping(value = "/validate", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<?> validate(@RequestPart("photo") MultipartFile photo,
            @RequestHeader(value = "X-Correlation-ID", required = false) String suppliedId) throws IOException {
        String correlationId = suppliedId != null && suppliedId.matches("[A-Za-z0-9_-]{1,64}")
                ? suppliedId : UUID.randomUUID().toString();
        if (photo.isEmpty() || photo.getSize() > 10 * 1024 * 1024L ||
                !("image/png".equals(photo.getContentType()) || "image/jpeg".equals(photo.getContentType()))) {
            return ResponseEntity.badRequest().body(Map.of("error", "Unsupported or oversized image",
                    "correlationId", correlationId));
        }
        log.info("GDAI-BACK validation requested correlationId={} bytes={}", correlationId, photo.getSize());
        try {
            // The classifier endpoint must be implemented in GDAI-VALID before end-to-end use.
            byte[] image = photo.getBytes();
            Map<?, ?> result = validClient.post().uri("/classify-garden")
                    .header("X-Correlation-ID", correlationId)
                    .contentType(MediaType.parseMediaType(photo.getContentType()))
                    .body(image).retrieve().body(Map.class);
            log.info("GDAI-BACK validation completed correlationId={}", correlationId);
            return ResponseEntity.ok().header("X-Correlation-ID", correlationId)
                    .body(Map.of("correlationId", correlationId, "validation", result == null ? Map.of() : result,
                            "requiresConfirmation", true));
        } catch (org.springframework.web.client.RestClientException ex) {
            log.warn("GDAI-VALID unavailable correlationId={} reason={}", correlationId, ex.getClass().getSimpleName());
            return ResponseEntity.status(503).body(Map.of("error", "GDAI-VALID unavailable",
                    "correlationId", correlationId));
        }
    }
}
