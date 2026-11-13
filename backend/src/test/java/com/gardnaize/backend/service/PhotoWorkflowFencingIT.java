package com.gardnaize.backend.service;

import static org.junit.jupiter.api.Assertions.*;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;

/** PostgreSQL transaction-level fencing: stale workers cannot mutate photo or history. */
@SpringBootTest(properties = {
    "gardnaize.workflow.poll-ms=3600000",
    "gardnaize.workflow.initial-delay-ms=3600000",
    "gardnaize.vision.enabled=false"
})
class PhotoWorkflowFencingIT {
    @Autowired JdbcTemplate jdbc;
    @Autowired PhotoWorkflowFencingService fenced;
    @Autowired PhotoWorkflowMaster master;

    @Test
    void expiredLeaseRejectsPhotoModuleAndVisionWritesWithoutAuditSideEffects() {
        UUID garden = UUID.randomUUID(), photo = UUID.randomUUID(), request = UUID.randomUUID();
        jdbc.update("INSERT INTO garden_projects(id,name,location,exposure,soil_type,created_at) VALUES (?,?,?,?,?,now())",
                garden, "Fencing", "Paris", "FULL_SUN", "LOAMY");
        try {
            jdbc.update("""
                INSERT INTO garden_photos(id,garden_id,original_filename,content_type,file_size_bytes,
                    width_px,height_px,image_bytes,photo_status,processing_status)
                VALUES (?,?,'garden.webp','image/webp',12,640,480,?,'RECEIVED','INITIALIZED')
                """, photo, garden, new byte[12]);
            jdbc.update("""
                INSERT INTO garden_photo_requests
                  (request_id,garden_id,photo_id,status,lease_owner,lease_until,lease_generation)
                VALUES (?,?,?,'RUNNING','owner-a',now()+interval '90 seconds',7)
                """, request, garden, photo);
            var old = new PhotoWorkflowFencingService.Lease(request, "owner-a", 7);
            fenced.photoTransition(old, photo, "VALIDATING", "VALIDATION_STARTED");
            UUID run = fenced.moduleStarted(old, "VALID");
            jdbc.update("""
                UPDATE garden_photo_requests SET lease_until=now()-interval '1 second'
                WHERE request_id=?
                """, request);
            assertEquals(1, master.reconcileExpired());
            assertThrows(PhotoWorkflowFencingService.LeaseLostException.class,
                    () -> fenced.photoTransition(old, photo, "VALID", "VALIDATION_COMPLETED"));
            assertThrows(PhotoWorkflowFencingService.LeaseLostException.class,
                    () -> fenced.moduleFinished(old, run, "VALID", "COMPLETED", null));
            assertThrows(PhotoWorkflowFencingService.LeaseLostException.class,
                    () -> fenced.saveVision(old, photo, "{\"isGarden\":true}"));
            assertThrows(PhotoWorkflowFencingService.LeaseLostException.class,
                    () -> fenced.requestTransition(old, "COMPLETED", "WORKFLOW_COMPLETED", null));
            assertEquals("VALIDATING", jdbc.queryForObject(
                    "SELECT workflow_status FROM garden_photos WHERE id=?", String.class, photo));
            assertEquals("RUNNING", jdbc.queryForObject(
                    "SELECT status FROM garden_photo_module_runs WHERE id=?", String.class, run));
            assertEquals(0, jdbc.queryForObject("""
                SELECT count(*) FROM garden_photo_request_history
                WHERE request_id=? AND event_code='WORKFLOW_COMPLETED'
                """, Integer.class, request));
            assertEquals("RECONCILIATION_REQUIRED", jdbc.queryForObject(
                    "SELECT status FROM garden_photo_requests WHERE request_id=?", String.class, request));
        } finally {
            jdbc.update("DELETE FROM garden_projects WHERE id=?", garden);
        }
    }
}
