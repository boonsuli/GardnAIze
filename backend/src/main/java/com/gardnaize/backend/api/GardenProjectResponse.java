package com.gardnaize.backend.api;

import com.gardnaize.backend.domain.Exposure;
import com.gardnaize.backend.domain.GardenProject;
import com.gardnaize.backend.domain.SoilType;
import java.time.Instant;
import java.util.UUID;

public record GardenProjectResponse(
        UUID id,
        String name,
        String location,
        Exposure exposure,
        SoilType soilType,
        Instant createdAt
) {
    public static GardenProjectResponse from(GardenProject project) {
        return new GardenProjectResponse(
                project.getId(),
                project.getName(),
                project.getLocation(),
                project.getExposure(),
                project.getSoilType(),
                project.getCreatedAt()
        );
    }
}
