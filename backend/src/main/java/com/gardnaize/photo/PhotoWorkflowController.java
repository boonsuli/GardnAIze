package com.gardnaize.photo;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.constraints.NotBlank;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/v1/gardens/photos")
@Tag(name = "Garden photo workflow", description = "Upload, ResNet-18 validation and asynchronous vision orchestration")
public class PhotoWorkflowController {
    private final PhotoWorkflowService service;

    public PhotoWorkflowController(PhotoWorkflowService service) { this.service = service; }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Operation(summary = "Validate a garden photo; persist and start vision only if valid")
    public ResponseEntity<PhotoContracts.PhotoResponse> submit(
            @RequestPart("photo") MultipartFile photo,
            @RequestPart("description") String description) {
        var result = service.submit(photo, description);
        return ResponseEntity.status(result.valid() ? HttpStatus.ACCEPTED : HttpStatus.UNPROCESSABLE_ENTITY)
                .body(result);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Poll photo and vision processing status")
    public PhotoContracts.PhotoStatus status(@PathVariable UUID id) { return service.status(id); }

    @GetMapping("/{id}/vision")
    @Operation(summary = "Retrieve vision analysis when available")
    public PhotoContracts.VisionResponse vision(@PathVariable UUID id) { return service.vision(id); }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<PhotoContracts.ApiError> badRequest(IllegalArgumentException e) {
        return ResponseEntity.badRequest().body(new PhotoContracts.ApiError("INVALID_UPLOAD", e.getMessage()));
    }

    @ExceptionHandler(PhotoWorkflowService.PhotoNotFoundException.class)
    public ResponseEntity<PhotoContracts.ApiError> missing(RuntimeException e) {
        return ResponseEntity.status(404).body(new PhotoContracts.ApiError("NOT_FOUND", e.getMessage()));
    }

    @ExceptionHandler(IllegalStateException.class)
    public ResponseEntity<PhotoContracts.ApiError> upstream(RuntimeException e) {
        return ResponseEntity.status(503).body(new PhotoContracts.ApiError("UPSTREAM_UNAVAILABLE", e.getMessage()));
    }
}
