package com.gardnaize.backend.service;

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
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

/** Adapter for the real GDAI-VALID FastAPI /api/v1/validation/photo contract. */
@Service
public class PhotoValidationService {
    private final RestClient client;

    public PhotoValidationService(
            @Value("${gardnaize.validation.base-url:http://localhost:9001}") String baseUrl) {
        var factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofSeconds(3));
        factory.setReadTimeout(Duration.ofSeconds(30));
        client = RestClient.builder().baseUrl(baseUrl).requestFactory(factory).build();
    }

    public Map<String, Object> validate(MultipartFile file) {
        if (file == null || file.isEmpty() || file.getSize() > 5L * 1024 * 1024) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Photo must be 1 byte to 5 MiB");
        }
        if (!Set.of("image/jpeg", "image/png", "image/webp").contains(file.getContentType())) {
            throw new ResponseStatusException(HttpStatus.UNSUPPORTED_MEDIA_TYPE, "Unsupported photo type");
        }
        byte[] bytes;
        try {
            bytes = file.getBytes();
        } catch (IOException ex) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Cannot read photo", ex);
        }
        var headers = new HttpHeaders();
        headers.setContentType(MediaType.parseMediaType(file.getContentType()));
        var resource = new ByteArrayResource(bytes) {
            @Override public String getFilename() { return "garden-photo"; }
        };
        var parts = new LinkedMultiValueMap<String, Object>();
        parts.add("photo", new HttpEntity<>(resource, headers));
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> result = client.post().uri("/api/v1/validation/photo")
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(parts).retrieve().body(Map.class);
            if (result == null || !(result.get("valid") instanceof Boolean)
                    || !(result.get("status") instanceof String)
                    || !(result.get("confidence") instanceof Number)) {
                throw new ResponseStatusException(HttpStatus.BAD_GATEWAY, "Unexpected GDAI-VALID response");
            }
            return result;
        } catch (RestClientException ex) {
            throw new ResponseStatusException(HttpStatus.BAD_GATEWAY, "GDAI-VALID unavailable", ex);
        }
    }
}
