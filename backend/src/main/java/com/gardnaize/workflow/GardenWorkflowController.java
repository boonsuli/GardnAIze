package com.gardnaize.workflow;

import com.gardnaize.workflow.GardenWorkflowDtos.*;
import jakarta.validation.constraints.NotBlank;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.io.IOException;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/gardens")
public class GardenWorkflowController {
    private final GardenWorkflowService service;
    public GardenWorkflowController(GardenWorkflowService service) { this.service = service; }

    // Only the trusted GDAI-FRONT server should access this endpoint.
    @PostMapping(value="/photos/confirm", consumes=MediaType.MULTIPART_FORM_DATA_VALUE)
    public StoredPhoto confirm(@RequestPart("photo") MultipartFile photo,
                               @RequestPart(value="description", required=false) String description)
            throws IOException {
        return service.validateAndPersist(photo, description);
    }

    @GetMapping("/photos/{photoId}/questions")
    public Questionnaire questions(@PathVariable UUID photoId,
            @RequestParam(defaultValue="fr") String language,
            @RequestParam(defaultValue="EU") String continent,
            @RequestParam(defaultValue="TEMPERATE") String climate,
            @RequestParam(defaultValue="FR") String country) {
        return service.questions(photoId, language, continent, climate, country);
    }

    @PostMapping("/photos/{photoId}/answers")
    public AnswersResult answers(@PathVariable UUID photoId,
            @RequestParam(defaultValue="fr") String language,
            @RequestParam(defaultValue="EU") String continent,
            @RequestParam(defaultValue="TEMPERATE") String climate,
            @RequestParam(defaultValue="FR") String country,
            @RequestBody AnswersRequest request) {
        return service.saveAnswers(photoId, request.answers(), language, continent, climate, country);
    }
}
