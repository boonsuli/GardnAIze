package com.gardnaize.backend.service;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.bean.override.mockito.MockitoBean;

/** PostgreSQL-backed master claim integration: no external HTTP requests. */
@SpringBootTest(properties = {
        "gardnaize.workflow.poll-ms=3600000",
        "gardnaize.workflow.initial-delay-ms=3600000",
        "gardnaize.vision.enabled=false"
})
class PhotoWorkflowMasterIT {
    @Autowired JdbcTemplate jdbc;
    @Autowired PhotoWorkflowMaster master;
    @MockitoBean PhotoWorkflowWorker worker;

    @Test
    void claimedRequestIsNotDispatchedTwice() {
        UUID gardenId = UUID.randomUUID();
        UUID photoId = UUID.randomUUID();
        UUID requestId = UUID.randomUUID();
        jdbc.update("INSERT INTO garden_projects(id,name,location,exposure,soil_type,created_at) VALUES (?,?,?,?,?,now())",
                gardenId, "Master integration", "Paris", "FULL_SUN", "LOAMY");
        try {
            jdbc.update("""
                INSERT INTO garden_photos(id,garden_id,original_filename,content_type,file_size_bytes,
                  width_px,height_px,image_bytes,photo_status,processing_status)
                VALUES (?,?, 'test.webp','image/webp',12,640,480,?,'RECEIVED','INITIALIZED')
                """, photoId, gardenId, new byte[12]);
            jdbc.update("""
                INSERT INTO garden_photo_requests(request_id,garden_id,photo_id,status)
                VALUES (?,?,?,'ACCEPTED')
                """, requestId, gardenId, photoId);
            when(worker.execute(requestId, photoId)).thenReturn(CompletableFuture.completedFuture(null));
            master.dispatch();
            master.dispatch();
            assertEquals("RUNNING", jdbc.queryForObject(
                    "SELECT status FROM garden_photo_requests WHERE request_id=?", String.class, requestId));
            assertEquals(1, jdbc.queryForObject(
                    "SELECT attempt_count FROM garden_photo_requests WHERE request_id=?", Integer.class, requestId));
            verify(worker, times(1)).execute(requestId, photoId);
        } finally {
            jdbc.update("DELETE FROM garden_projects WHERE id=?", gardenId);
        }
    }
}
