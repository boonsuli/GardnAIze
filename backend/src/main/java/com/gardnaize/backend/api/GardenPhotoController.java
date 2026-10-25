package com.gardnaize.backend.api;

import com.gardnaize.backend.service.GardenPhotoService;
import io.swagger.v3.oas.annotations.Operation;
import java.util.UUID;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/v1/gardens/{gardenId}/photos")
public class GardenPhotoController {
    private final GardenPhotoService service;

    public GardenPhotoController(GardenPhotoService service) {
        this.service = service;
    }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Operation(summary = "Persist and analyze a garden photo with the configured external provider")
    public PhotoAnalysisResponse upload(@PathVariable UUID gardenId,
            @RequestPart("file") MultipartFile file) {
        return service.upload(gardenId, file);
    }

    @GetMapping("/{photoId}")
    @Operation(summary = "Get photo status and external analysis JSON")
    public PhotoAnalysisResponse get(@PathVariable UUID gardenId, @PathVariable UUID photoId) {
        return service.get(photoId, gardenId);
    }
}
