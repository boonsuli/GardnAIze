package com.gardnaize.photo;

import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PhotoSubmissionRepository extends JpaRepository<PhotoSubmission, UUID> {
}
