package com.gardnaize.backend.service;

import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.Map;
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
    private final Map<UUID, CompletableFuture<Void>> active = new ConcurrentHashMap<>();
    private final Map<UUID, Long> generations = new ConcurrentHashMap<>();

    public PhotoWorkflowMaster(JdbcTemplate jdbc, PhotoWorkflowWorker worker,
                               PhotoWorkflowStateService states) {
        this.jdbc = jdbc;
        this.worker = worker;
        this.states = states;
    }

    @Scheduled(fixedDelayString = "${gardnaize.workflow.poll-ms:5000}",
            initialDelayString = "${gardnaize.workflow.initial-delay-ms:5000}")
    public void dispatch() {
        // SKIP LOCKED ensures two application instances never claim the same row.
        // Do not reclaim expired RUNNING work automatically: the remote call may still be active.
        // A dedicated idempotent retry protocol is required before replay is safe.
        var claimed = jdbc.query("""
            WITH candidate AS (
                SELECT request_id FROM public.garden_photo_requests
                WHERE status='ACCEPTED'
                ORDER BY created_at
                LIMIT 1 FOR UPDATE SKIP LOCKED
            )
            UPDATE public.garden_photo_requests r
            SET status='RUNNING', attempt_count=r.attempt_count+1,
                lease_generation=r.lease_generation+1,
                lease_owner=?, lease_until=now()+interval '180 seconds', updated_at=now()
            FROM candidate c WHERE r.request_id=c.request_id
            RETURNING r.request_id,r.photo_id,r.attempt_count,r.lease_generation
            """, (rs, row) -> new Claimed(
                    (UUID) rs.getObject(1), (UUID) rs.getObject(2), rs.getInt(3), rs.getLong(4)), owner);
        for (var item : claimed) {
            try {
                jdbc.update("""
                    INSERT INTO public.garden_photo_request_history
                        (request_id,previous_status,status,event_code)
                    VALUES (?,'ACCEPTED','RUNNING','WORKER_CLAIMED')
                    """, item.requestId());
                log.info("event=WORKER_CLAIMED requestId={} photoId={} attempt={}",
                        item.requestId(), item.photoId(), item.attempt());
                var future = worker.execute(item.requestId(), item.photoId(),
                        new PhotoWorkflowFencingService.Lease(item.requestId(), owner, item.generation()));
                active.put(item.requestId(), future);
                generations.put(item.requestId(), item.generation());
                future.whenComplete((result, failure) -> {
                    active.remove(item.requestId(), future);
                    generations.remove(item.requestId(), item.generation());
                });
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
        reconcileExpired();
    }


    @Scheduled(fixedDelayString = "${gardnaize.workflow.heartbeat-ms:30000}",
            initialDelayString = "${gardnaize.workflow.heartbeat-ms:30000}")
    public void heartbeat() {
        active.forEach((requestId, future) -> {
            if (future.isDone()) return;
            int updated = jdbc.update("""
                UPDATE public.garden_photo_requests SET lease_until=now()+interval '180 seconds'
                WHERE request_id=? AND lease_owner=? AND status='RUNNING'
                  AND lease_until > now() AND lease_generation=?
                """, requestId, owner, generations.getOrDefault(requestId, -1L));
            if (updated == 0) log.warn("event=LEASE_LOST requestId={}", requestId);
        });
    }

    /** Ambiguous remote calls are quarantined, never automatically billed twice. */
    public int reconcileExpired() {
        var expired = jdbc.query("""
            WITH expired AS (
                SELECT request_id FROM public.garden_photo_requests
                WHERE status='RUNNING' AND lease_until < now()
                ORDER BY lease_until LIMIT 100 FOR UPDATE SKIP LOCKED
            )
            UPDATE public.garden_photo_requests r
            SET status='RECONCILIATION_REQUIRED',lease_owner=NULL,lease_until=NULL,
                lease_generation=r.lease_generation+1,updated_at=now()
            FROM expired e WHERE r.request_id=e.request_id
            RETURNING r.request_id
            """, (rs, index) -> (UUID) rs.getObject(1));
        for (UUID requestId : expired) {
            jdbc.update("""
                INSERT INTO public.garden_photo_request_history
                    (request_id,previous_status,status,event_code,error_code)
                VALUES (?,'RUNNING','RECONCILIATION_REQUIRED','LEASE_EXPIRED','RECOVERY_REVIEW_REQUIRED')
                """, requestId);
            log.warn("event=LEASE_EXPIRED requestId={} status=RECONCILIATION_REQUIRED", requestId);
        }
        return expired.size();
    }

    private record Claimed(UUID requestId, UUID photoId, int attempt, long generation) {}
}
