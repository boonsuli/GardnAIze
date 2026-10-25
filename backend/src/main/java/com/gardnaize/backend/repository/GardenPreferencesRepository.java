package com.gardnaize.backend.repository;

import com.gardnaize.backend.domain.GardenPreferences;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface GardenPreferencesRepository extends JpaRepository<GardenPreferences, UUID> {
}
