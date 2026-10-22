package com.gardnaize.backend.api;

import com.gardnaize.backend.domain.Exposure;
import com.gardnaize.backend.domain.SoilType;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record CreateGardenProjectRequest(
        @NotBlank @Size(max = 120) String name,
        @NotBlank @Size(max = 160) String location,
        @NotNull Exposure exposure,
        @NotNull SoilType soilType
) {
}
