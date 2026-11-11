package com.gardnaize.backend.api;

import java.io.IOException;
import java.time.Duration;
import java.util.Map;
import java.util.Set;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.multipart.MultipartFile;

/** Stateless preflight: never persists the image and never calls Gemini Vision. */
@RestController
@RequestMapping("/api/v1/photos")
public class PhotoPreflightController {
    private final RestClient validator;

    public PhotoPreflightController(
            @Value("${gardnaize.validation.base-url:http://localhost:9001}") String url) {
        var factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofSeconds(3));
        factory.setReadTimeout(Duration.ofSeconds(30));
        validator = RestClient.builder().baseUrl(url).requestFactory(factory).build();
    }

    @PostMapping(value = "/validate", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Map<String, Object> validate(@RequestPart("file") MultipartFile file) throws IOException {
        if (file.isEmpty() || file.getSize() > 5L * 1024 * 1024) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Photo must be 1 byte to 5 MiB");
        }
        if (!Set.of("image/jpeg", "image/png", "image/webp").contains(file.getContentType())) {
            throw new ResponseStatusException(HttpStatus.UNSUPPORTED_MEDIA_TYPE, "Unsupported photo type");
        }
        var headers = new HttpHeaders();
        headers.setContentType(MediaType.parseMediaType(file.getContentType()));
        var bytes = file.getBytes();
        var resource = new ByteArrayResource(bytes) {
            @Override
            public String getFilename() {
                return "garden-photo";
            }
        };
        var parts = new LinkedMultiValueMap<String, Object>();
        parts.add("file", new HttpEntity<>(resource, headers));
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> result = validator.post().uri("/validate")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(parts).retrieve().body(Map.class);
            if (result == null) {
                throw new ResponseStatusException(HttpStatus.BAD_GATEWAY, "Empty validator response");
            }
            Object valid = result.get("valid");
            if (!(valid instanceof Boolean)) {
                throw new ResponseStatusException(HttpStatus.BAD_GATEWAY, "Unexpected validator contract");
            }
            return Map.of("valid", valid, "reason", String.valueOf(result.getOrDefault("reason", "")));
        } catch (org.springframework.web.client.RestClientException ex) {
            throw new ResponseStatusException(HttpStatus.BAD_GATEWAY, "GDAI-VALID unavailable", ex);
        }
    }
}
