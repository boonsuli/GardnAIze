package com.gardnaize.backend.api;

import com.fasterxml.jackson.databind.JsonNode;
import com.gardnaize.backend.service.StagedPhotoIntakeService;
import io.swagger.v3.oas.annotations.Operation;
import java.net.URI;
import java.util.UUID;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

/** Additive staged intake endpoints; PR35 legacy endpoint remains unchanged. */
@RestController
@RequestMapping("/api/v1/gardens/{gardenId}")
public class StagedPhotoIntakeController {
    private final StagedPhotoIntakeService intake;

    public StagedPhotoIntakeController(StagedPhotoIntakeService intake) {
        this.intake = intake;
    }

    @PostMapping(value="/photos/staged", consumes=MediaType.MULTIPART_FORM_DATA_VALUE)
    @Operation(summary="Accept a confirmed photo with external-processing consent, queue VALID/VISION, and return 202")
    public ResponseEntity<PhotoProcessingRequestResponse> start(
            @PathVariable UUID gardenId,
            @RequestPart("file") MultipartFile file,
            @RequestPart(value="description", required=false) String description,
            @RequestParam("consentKey") String consentKey,
            @RequestParam(value="trainingConsent", defaultValue="false") boolean trainingConsent) {
        var accepted = intake.start(gardenId, file, description, consentKey, trainingConsent);
        return ResponseEntity.accepted().location(URI.create(accepted.statusUrl()))
                .header("Retry-After", "2").body(accepted);
    }

    @PutMapping(value="/photo-requests/{requestId}/answers",
            consumes=MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary="Submit final questionnaire answers after VISION was queued")
    public ResponseEntity<Void> submitAnswers(
            @PathVariable UUID gardenId, @PathVariable UUID requestId,
            @RequestBody JsonNode answers) {
        intake.submitAnswers(gardenId, requestId, answers);
        return ResponseEntity.noContent().build();
    }
}
