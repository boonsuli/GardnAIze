package com.gardnaize.backend.api;

import com.gardnaize.backend.service.GardenPhotoService;
import com.gardnaize.backend.service.PhotoProcessingRequestService;
import org.springframework.http.ResponseEntity;
import java.net.URI;
import io.swagger.v3.oas.annotations.Operation;
import java.util.UUID;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/v1/gardens/{gardenId}/photos")
public class GardenPhotoController {
    private final GardenPhotoService service;
    private final PhotoProcessingRequestService requests;

    public GardenPhotoController(GardenPhotoService service, PhotoProcessingRequestService requests) {
        this.service = service;
        this.requests = requests;
    }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Operation(summary = "Accept a garden photo processing request",
            description = "Persists the photo, questionnaire, consent and request audit. Returns 202 without waiting for external analysis.")
    @io.swagger.v3.oas.annotations.responses.ApiResponse(responseCode = "202", description = "Request persisted")
    public ResponseEntity<PhotoProcessingRequestResponse> upload(@PathVariable UUID gardenId,
            @RequestPart("file") MultipartFile file,
            @RequestPart(value = "description", required = false) String description,
            @RequestParam("answersJson") String answersJson,
            @RequestParam("consentKey") String consentKey) {
        var accepted = requests.accept(gardenId, file, description, answersJson, consentKey);
        return ResponseEntity.accepted().location(URI.create(accepted.statusUrl()))
                .header("Retry-After", "2").body(accepted);
    }

    @GetMapping("/{photoId}")
    @Operation(summary = "Get photo status and external analysis JSON")
    public PhotoAnalysisResponse get(@PathVariable UUID gardenId, @PathVariable UUID photoId) {
        return service.get(photoId, gardenId);
    }
}
