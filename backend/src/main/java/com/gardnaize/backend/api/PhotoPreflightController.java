package com.gardnaize.backend.api;

import com.gardnaize.backend.service.PhotoValidationService;
import io.swagger.v3.oas.annotations.Operation;
import java.util.Map;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

/** Stateless preflight: never persists the image and never calls Gemini Vision. */
@RestController
@RequestMapping("/api/v1/photos")
public class PhotoPreflightController {
    private final PhotoValidationService validationService;

    public PhotoPreflightController(PhotoValidationService validationService) {
        this.validationService = validationService;
    }

    @PostMapping(value = "/validate", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Operation(summary = "Validate a garden image using GDAI-VALID ResNet-18",
            description = "Forwards the multipart photo to GDAI-VALID. Does not persist the image.")
    public Map<String, Object> validate(@RequestPart("file") MultipartFile file) {
        return validationService.validate(file);
    }
}
