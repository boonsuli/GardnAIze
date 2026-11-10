package com.gardnaize.photo;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.net.URI;
import java.time.Duration;
import java.util.UUID;
import java.util.concurrent.Executor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

@Service
public class PhotoWorkflowService {
    private final PhotoSubmissionRepository repository;
    private final RestClient validClient;
    private final RestClient visionClient;
    private final ObjectMapper mapper;
    private final Executor executor;

    public PhotoWorkflowService(PhotoSubmissionRepository repository, ObjectMapper mapper,
            @Value("${gardnaize.photo.valid-url:http://localhost:8000/classify-garden}") String validUrl,
            @Value("${gardnaize.photo.vision-url:http://localhost:8000/analyze}") String visionUrl) {
        this.repository = repository;
        this.mapper = mapper;
        var factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofSeconds(3));
        factory.setReadTimeout(Duration.ofSeconds(30));
        this.validClient = RestClient.builder().requestFactory(factory).baseUrl(validUrl).build();
        this.visionClient = RestClient.builder().requestFactory(factory).baseUrl(visionUrl).build();
        var pool = new ThreadPoolTaskExecutor();
        pool.setCorePoolSize(2);
        pool.setMaxPoolSize(4);
        pool.setQueueCapacity(100);
        pool.setThreadNamePrefix("gdai-vision-");
        pool.initialize();
        this.executor = pool;
    }

    public PhotoContracts.PhotoResponse submit(MultipartFile file, String description) {
        if (file.isEmpty() || file.getSize() > 1_048_576L) {
            throw new IllegalArgumentException("Photo obligatoire, taille maximale 1 Mo");
        }
        String type = file.getContentType();
        if (!MediaType.IMAGE_JPEG_VALUE.equals(type) && !MediaType.IMAGE_PNG_VALUE.equals(type)) {
            throw new IllegalArgumentException("Format accepté : JPEG ou PNG");
        }
        if (description == null || description.isBlank() || description.length() > 2000) {
            throw new IllegalArgumentException("Description obligatoire (2000 caractères maximum)");
        }
        try {
            byte[] bytes = file.getBytes();
            // Fail closed: unavailable or malformed classifier responses must never be treated as valid.
            JsonNode result = validClient.post().contentType(MediaType.parseMediaType(type))
                    .body(bytes).retrieve().body(JsonNode.class);
            if (result == null || !result.has("valid") || !result.get("valid").isBoolean()) {
                throw new IllegalStateException("Contrat GDAI-VALID incompatible : booléen valid attendu");
            }
            if (!result.get("valid").asBoolean()) {
                return new PhotoContracts.PhotoResponse(null, "INVALID", "Photo non valide", false);
            }
            UUID id = UUID.randomUUID();
            repository.save(new PhotoSubmission(id, description.trim(), type,
                    file.getOriginalFilename() == null ? "garden" : file.getOriginalFilename(), bytes));
            executor.execute(() -> analyze(id, bytes, type));
            return new PhotoContracts.PhotoResponse(id, "VISION_PENDING", "Photo valide", true);
        } catch (java.io.IOException e) {
            throw new IllegalArgumentException("Lecture de la photo impossible", e);
        } catch (RestClientException e) {
            throw new IllegalStateException("Service IA indisponible", e);
        }
    }

    @Transactional(readOnly = true)
    public PhotoContracts.PhotoStatus status(UUID id) {
        var photo = repository.findById(id).orElseThrow(() -> new PhotoNotFoundException(id));
        return new PhotoContracts.PhotoStatus(id, photo.getStatus(), message(photo.getStatus()));
    }

    @Transactional(readOnly = true)
    public PhotoContracts.VisionResponse vision(UUID id) {
        var photo = repository.findById(id).orElseThrow(() -> new PhotoNotFoundException(id));
        return new PhotoContracts.VisionResponse(id, photo.getStatus(), photo.getVisionJson());
    }

    private void analyze(UUID id, byte[] bytes, String type) {
        try {
            String result = visionClient.post().contentType(MediaType.parseMediaType(type))
                    .body(bytes).retrieve().body(String.class);
            if (result == null || result.isBlank()) throw new IllegalStateException("Empty vision response");
            mapper.readTree(result);
            updateVision(id, result, true);
        } catch (Exception e) {
            updateVision(id, null, false);
        }
    }

    private void updateVision(UUID id, String json, boolean success) {
        repository.findById(id).ifPresent(photo -> {
            if (success) photo.markVisionComplete(json);
            else photo.markVisionFailed();
            repository.save(photo);
        });
    }

    private String message(String status) {
        return switch (status) {
            case "VISION_COMPLETED" -> "Analyse du jardin terminée";
            case "VISION_FAILED" -> "Analyse du jardin indisponible";
            default -> "Photo valide, analyse en cours";
        };
    }

    public static class PhotoNotFoundException extends RuntimeException {
        public PhotoNotFoundException(UUID id) { super("Photo introuvable : " + id); }
    }
}
