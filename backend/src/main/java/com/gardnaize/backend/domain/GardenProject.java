package com.gardnaize.backend.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "garden_projects", schema = "public")
public class GardenProject {
    @Id
    private UUID id;
    @Column(nullable = false, length = 120)
    private String name;
    @Column(nullable = false, length = 160)
    private String location;
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 24)
    private Exposure exposure;
    @Enumerated(EnumType.STRING)
    @Column(name = "soil_type", nullable = false, length = 24)
    private SoilType soilType;
    @Column(name = "country_code", nullable = false, length = 8)
    private String countryCode;
    @Column(name = "climate_region", nullable = false, length = 120)
    private String climateRegion;
    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected GardenProject() {}

    public GardenProject(String name, String location, Exposure exposure, SoilType soilType,
            String countryCode, String climateRegion) {
        this.id = UUID.randomUUID();
        this.name = name;
        this.location = location;
        this.exposure = exposure;
        this.soilType = soilType;
        this.countryCode = countryCode == null ? "FR" : countryCode;
        this.climateRegion = climateRegion == null || climateRegion.isBlank()
                ? "UNKNOWN" : climateRegion;
        this.createdAt = Instant.now();
    }

    public UUID getId() { return id; }
    public String getName() { return name; }
    public String getLocation() { return location; }
    public Exposure getExposure() { return exposure; }
    public SoilType getSoilType() { return soilType; }
    public String getCountryCode() { return countryCode; }
    public String getClimateRegion() { return climateRegion; }
    public Instant getCreatedAt() { return createdAt; }
}
