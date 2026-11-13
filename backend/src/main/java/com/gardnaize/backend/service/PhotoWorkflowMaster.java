package com.gardnaize.backend.service;

import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

/** Database-backed master: claims one request atomically; no in-memory-only queue. */
@Service
@EnableScheduling
public class PhotoWorkflowMaster {
    private static final Logger log = LoggerFactory.getLogger(PhotoWorkflowMaster.class);
    private final JdbcTemplate jdbc;
    private final PhotoWorkflowWorker worker;
    private final PhotoWorkflowStateService states;
    private final String owner = UUID.randomUUID().toString();

    public PhotoWorkflowMaster(JdbcTemplate jdbc, PhotoWorkflowWorker worker,
                               PhotoWorkflowStateService states) {
        this.jdbc = jdbc;
        this.worker = worker;
        this.states = states;
    }

    @Scheduled(fixedDelayString = "${gardnaize.workflow.poll-ms:5000}")
    public void dispatch() {
        // Expired leases are only reclaimed up to the configured attempt ceiling.
        // SKIP LOCKED ensures two application instances never claim the same row.
        var claimed = jdbc.query("""
            WITH candidate AS (
                SELECT request_id FROM public.garden_photo_requests
                WHERE status='ACCEPTED'
                   OR (status='RUNNING' AND lease_until < now() AND attempt_count < 3)
                ORDER BY created_at
                LIMIT 1 FOR UPDATE SKIP LOCKED
            )
            UPDATE public.garden_photo_requests r
            SET status='RUNNING', attempt_count=r.attempt_count+1,
                lease_owner=?, lease_until=now()+interval '180 seconds', updated_at=now()
            FROM candidate c WHERE r.request_id=c.request_id
            RETURNING r.request_id,r.photo_id,r.attempt_count
            """, (rs, row) -> new Claimed(
                    (UUID) rs.getObject(1), (UUID) rs.getObject(2), rs.getInt(3)), owner);
        for (var item : claimed) {
            try {
                jdbc.update("""
                    INSERT INTO public.garden_photo_request_history
                        (request_id,previous_status,status,event_code)
                    VALUES (?,'ACCEPTED','RUNNING','WORKER_CLAIMED')
                    """, item.requestId());
                log.info("event=WORKER_CLAIMED requestId={} photoId={} attempt={}",
                        item.requestId(), item.photoId(), item.attempt());
                worker.execute(item.requestId(), item.photoId());
            } catch (RuntimeException ex) {
                log.error("event=WORKER_DISPATCH_FAILED requestId={} errorType={}",
                        item.requestId(), ex.getClass().getSimpleName());
                try {
                    states.requestTransition(item.requestId(), "RUNNING", "FAILED",
                            "WORKER_DISPATCH_FAILED", "DISPATCH_ERROR");
                } catch (RuntimeException stateError) {
                    log.error("event=WORKER_STATE_WRITE_FAILED requestId={} errorType={}",
                            item.requestId(), stateError.getClass().getSimpleName());
                }
            }
        }
        // Exhausted leases are made terminal rather than left in RUNNING indefinitely.
        jdbc.update("""
            UPDATE public.garden_photo_requests SET status='FAILED',lease_owner=NULL,
                lease_until=NULL,finished_at=now(),updated_at=now()
            WHERE status='RUNNING' AND lease_until < now() AND attempt_count >= 3
            """);
    }

    private record Claimed(UUID requestId, UUID photoId, int attempt) {}
}
