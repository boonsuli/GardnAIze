package com.gardnaize.backend.api;

import com.gardnaize.backend.domain.GardenPreferences;
import com.gardnaize.backend.repository.GardenPreferencesRepository;
import com.gardnaize.backend.repository.GardenProjectRepository;
import jakarta.validation.Valid;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/v1/gardens/{gardenId}/preferences")
public class GardenPreferencesController {
    private final GardenPreferencesRepository preferencesRepository;
    private final GardenProjectRepository gardenRepository;

    public GardenPreferencesController(GardenPreferencesRepository preferencesRepository,
            GardenProjectRepository gardenRepository) {
        this.preferencesRepository = preferencesRepository;
        this.gardenRepository = gardenRepository;
    }

    @GetMapping
    @Transactional(readOnly = true)
    public GardenPreferencesResponse get(@PathVariable UUID gardenId) {
        return preferencesRepository.findById(gardenId)
                .map(GardenPreferencesResponse::from)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND,
                        "Garden preferences not found"));
    }

    @PutMapping
    @Transactional
    public GardenPreferencesResponse put(@PathVariable UUID gardenId,
            @Valid @RequestBody GardenPreferencesRequest request) {
        if (!gardenRepository.existsById(gardenId)) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Garden project not found");
        }
        GardenPreferences preferences = preferencesRepository.findById(gardenId)
                .orElseGet(() -> new GardenPreferences(gardenId, request.waterAvailability(),
                        request.maintenancePreference(), request.evergreenPreferred(),
                        request.privacyScreeningRequired(), request.desiredHeightCm()));
        preferences.update(request.waterAvailability(), request.maintenancePreference(),
                request.evergreenPreferred(), request.privacyScreeningRequired(),
                request.desiredHeightCm());
        return GardenPreferencesResponse.from(preferencesRepository.save(preferences));
    }
}
