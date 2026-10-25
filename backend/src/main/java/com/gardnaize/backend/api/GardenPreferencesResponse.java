package com.gardnaize.backend.api;

import com.gardnaize.backend.domain.GardenPreferences;
import java.time.Instant;
import java.util.UUID;

public record GardenPreferencesResponse(
        UUID gardenId,
        String waterAvailability,
        String maintenancePreference,
        boolean evergreenPreferred,
        boolean privacyScreeningRequired,
        Integer desiredHeightCm,
        Instant updatedAt
) {
    public static GardenPreferencesResponse from(GardenPreferences preferences) {
        return new GardenPreferencesResponse(
                preferences.getGardenId(), preferences.getWaterAvailability(),
                preferences.getMaintenancePreference(), preferences.isEvergreenPreferred(),
                preferences.isPrivacyScreeningRequired(), preferences.getDesiredHeightCm(),
                preferences.getUpdatedAt()
        );
    }
}
