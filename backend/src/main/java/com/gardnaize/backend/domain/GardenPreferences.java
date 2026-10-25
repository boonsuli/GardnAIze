package com.gardnaize.backend.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "garden_preferences")
public class GardenPreferences {
    @Id
    @Column(name = "garden_id", nullable = false)
    private UUID gardenId;

    @Column(name = "water_availability", nullable = false, length = 16)
    private String waterAvailability;

    @Column(name = "maintenance_preference", nullable = false, length = 16)
    private String maintenancePreference;

    @Column(name = "evergreen_preferred", nullable = false)
    private boolean evergreenPreferred;

    @Column(name = "privacy_screening_required", nullable = false)
    private boolean privacyScreeningRequired;

    @Column(name = "desired_height_cm")
    private Integer desiredHeightCm;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected GardenPreferences() {
    }

    public GardenPreferences(UUID gardenId, String waterAvailability, String maintenancePreference,
            boolean evergreenPreferred, boolean privacyScreeningRequired, Integer desiredHeightCm) {
        this.gardenId = gardenId;
        update(waterAvailability, maintenancePreference, evergreenPreferred,
                privacyScreeningRequired, desiredHeightCm);
    }

    public void update(String waterAvailability, String maintenancePreference,
            boolean evergreenPreferred, boolean privacyScreeningRequired, Integer desiredHeightCm) {
        this.waterAvailability = waterAvailability;
        this.maintenancePreference = maintenancePreference;
        this.evergreenPreferred = evergreenPreferred;
        this.privacyScreeningRequired = privacyScreeningRequired;
        this.desiredHeightCm = desiredHeightCm;
        this.updatedAt = Instant.now();
    }

    public UUID getGardenId() { return gardenId; }
    public String getWaterAvailability() { return waterAvailability; }
    public String getMaintenancePreference() { return maintenancePreference; }
    public boolean isEvergreenPreferred() { return evergreenPreferred; }
    public boolean isPrivacyScreeningRequired() { return privacyScreeningRequired; }
    public Integer getDesiredHeightCm() { return desiredHeightCm; }
    public Instant getUpdatedAt() { return updatedAt; }
}
