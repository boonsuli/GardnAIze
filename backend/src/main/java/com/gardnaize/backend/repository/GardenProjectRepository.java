package com.gardnaize.backend.repository;

import com.gardnaize.backend.domain.GardenProject;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface GardenProjectRepository extends JpaRepository<GardenProject, UUID> {
}
