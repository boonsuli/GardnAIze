package com.gardnaize.workflow;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Controller;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.client.RestClient;
import org.springframework.web.server.ResponseStatusException;

import java.io.IOException;
import java.util.Map;
import java.util.Set;

@Controller
public class GardenPhotoIntakeController {
    private static final long MAX_BYTES = 5L * 1024 * 1024;
    private static final Set<String> CLIMATES = Set.of(
        "UNKNOWN", "OCEANIC", "CONTINENTAL", "MEDITERRANEAN", "HOT_DRY"
    );
    private static final Set<String> COUNTRIES = Set.of("FR", "BE", "CH", "ES", "IT", "OTHER");
    private final RestClient client;
    private final String validatorBaseUrl;

    public GardenPhotoIntakeController(RestClient.Builder builder,
            @Value("${gardnaize.validation.base-url:http://localhost:9001}") String validatorBaseUrl) {
        this.client = builder.build();
        this.validatorBaseUrl = validatorBaseUrl;
    }

    @PostMapping(value = "/api/v1/gardens/photos/confirm",
        consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @ResponseBody
    public Map<String, String> confirm(
            @RequestPart("photo") MultipartFile photo,
            @RequestParam String countryCode,
            @RequestParam String city,
            @RequestParam String climateCode,
            @RequestParam(defaultValue = "") String description) throws IOException {
        if (photo.isEmpty() || photo.getSize() > MAX_BYTES) {
            throw new ResponseStatusException(HttpStatus.PAYLOAD_TOO_LARGE, "Maximum 5 MiB");
        }
        if (!COUNTRIES.contains(countryCode) || !CLIMATES.contains(climateCode)
                || city.isBlank() || city.length() > 160 || description.length() > 1000) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Invalid garden location");
        }
        byte[] bytes = photo.getBytes();
        String mime = detectMime(bytes);
        if (mime == null) {
            throw new ResponseStatusException(HttpStatus.UNSUPPORTED_MEDIA_TYPE, "JPEG, PNG or WebP required");
        }
        var resource = new ByteArrayResource(bytes) {
            @Override
            public String getFilename() {
                return "garden-photo";
            }
        };
        var headers = new HttpHeaders();
        headers.setContentType(MediaType.parseMediaType(mime));
        var parts = new LinkedMultiValueMap<String, Object>();
        parts.add("photo", new HttpEntity<>(resource, headers));
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> response = client.post()
                .uri(validatorBaseUrl + "/validate")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(parts)
                .retrieve()
                .body(Map.class);
            if (response == null || !("VALID".equals(response.get("status")))) {
                return Map.of("status", "INVALID", "message", "Photo non valide");
            }
            // No durable image storage until the validated-photo persistence workflow is integrated.
            return Map.of("status", "VALID", "message", "Photo valide");
        } catch (Exception ex) {
            throw new ResponseStatusException(HttpStatus.BAD_GATEWAY, "GDAI-VALID unavailable", ex);
        }
    }

    private String detectMime(byte[] b) {
        if (b.length >= 3 && (b[0] & 255) == 255 && (b[1] & 255) == 216 && (b[2] & 255) == 255) {
            return "image/jpeg";
        }
        if (b.length >= 8 && (b[0] & 255) == 137 && b[1] == 80 && b[2] == 78 && b[3] == 71) {
            return "image/png";
        }
        if (b.length >= 12 && b[0] == 'R' && b[1] == 'I' && b[2] == 'F' && b[3] == 'F'
                && b[8] == 'W' && b[9] == 'E' && b[10] == 'B' && b[11] == 'P') {
            return "image/webp";
        }
        return null;
    }
}
