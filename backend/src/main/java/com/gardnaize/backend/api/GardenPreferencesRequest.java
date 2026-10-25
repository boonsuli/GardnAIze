package com.gardnaize.backend.api;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;

public record GardenPreferencesRequest(
        @NotNull @Pattern(regexp = "LOW|MODERATE|HIGH") String waterAvailability,
        @NotNull @Pattern(regexp = "LOW|MODERATE|HIGH") String maintenancePreference,
        @NotNull Boolean evergreenPreferred,
        @NotNull Boolean privacyScreeningRequired,
        @Min(20) @Max(3000) Integer desiredHeightCm
) {
}
