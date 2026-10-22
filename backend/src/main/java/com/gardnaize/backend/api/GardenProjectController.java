package com.gardnaize.backend.api;

import com.gardnaize.backend.service.GardenProjectService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.net.URI;
import java.util.List;
import java.util.UUID;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/gardens")
@Tag(name = "Gardens", description = "Garden projects and their questionnaire metadata")
public class GardenProjectController {
    private final GardenProjectService service;

    public GardenProjectController(GardenProjectService service) {
        this.service = service;
    }

    @PostMapping
    @Operation(summary = "Create a garden project")
    public ResponseEntity<GardenProjectResponse> create(
            @Valid @RequestBody CreateGardenProjectRequest request
    ) {
        GardenProjectResponse created = service.create(request);
        return ResponseEntity.created(URI.create("/api/v1/gardens/" + created.id()))
                .body(created);
    }

    @GetMapping
    @Operation(summary = "List garden projects")
    public List<GardenProjectResponse> list() {
        return service.list();
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get a garden project by ID")
    public GardenProjectResponse get(@PathVariable UUID id) {
        return service.get(id);
    }
}
