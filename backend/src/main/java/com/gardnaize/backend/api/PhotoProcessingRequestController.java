package com.gardnaize.backend.api;

import com.gardnaize.backend.service.PhotoProcessingRequestService;
import io.swagger.v3.oas.annotations.Operation;
import java.util.UUID;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/gardens/{gardenId}/photo-requests")
public class PhotoProcessingRequestController {
    private final PhotoProcessingRequestService requests;

    public PhotoProcessingRequestController(PhotoProcessingRequestService requests) {
        this.requests = requests;
    }

    @GetMapping("/{requestId}")
    @Operation(summary = "Get the current status of a persisted photo processing request")
    public PhotoProcessingRequestResponse get(@PathVariable UUID gardenId, @PathVariable UUID requestId) {
        return requests.get(gardenId, requestId);
    }
}
