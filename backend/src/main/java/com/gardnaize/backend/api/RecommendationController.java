package com.gardnaize.backend.api;

import com.gardnaize.backend.service.RecommendationService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.UUID;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/gardens")
@Tag(name = "Recommendations", description = "AI service orchestration")
public class RecommendationController {
    private final RecommendationService service;

    public RecommendationController(RecommendationService service) {
        this.service = service;
    }

    @GetMapping("/{id}/recommendations")
    @Operation(summary = "Request three preliminary plant suggestions from the AI service")
    public RecommendationResponse recommend(@PathVariable UUID id) {
        return service.recommend(id);
    }
}
