package com.gardnaize.backend.service;

import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Fenced writes. A SELECT FOR UPDATE on the request row serializes all module,
 * photo and history changes against lease expiry/reconciliation.
 */
@Service
public class PhotoWorkflowFencingService {
    private final JdbcTemplate jdbc;
    public PhotoWorkflowFencingService(JdbcTemplate jdbc) { this.jdbc = jdbc; }

    public record Lease(UUID requestId, String owner, long generation) {}

    public static class LeaseLostException extends RuntimeException {
        public LeaseLostException(UUID requestId) { super("Lease no longer owned for request " + requestId); }
    }

    private void requireLease(Lease lease) {
        Boolean valid = jdbc.queryForObject("""
            SELECT status='RUNNING' AND lease_owner=? AND lease_generation=?
                   AND lease_until > now()
            FROM public.garden_photo_requests WHERE request_id=? FOR UPDATE
            """, Boolean.class, lease.owner(), lease.generation(), lease.requestId());
        if (!Boolean.TRUE.equals(valid)) throw new LeaseLostException(lease.requestId());
    }

    @Transactional
    public UUID moduleStarted(Lease lease, String module) {
        requireLease(lease);
        UUID runId = UUID.randomUUID();
        jdbc.update("""
            INSERT INTO public.garden_photo_module_runs
              (id,request_id,module_name,status,attempt_number,started_at)
            VALUES (?,?,?,'RUNNING',
              (SELECT COALESCE(MAX(attempt_number),0)+1 FROM public.garden_photo_module_runs
               WHERE request_id=? AND module_name=?),now())
            """, runId, lease.requestId(), module, lease.requestId(), module);
        jdbc.update("""
            INSERT INTO public.garden_photo_request_history(request_id,module_name,status,event_code)
            VALUES (?,?,'RUNNING',?)
            """, lease.requestId(), module, module + "_STARTED");
        return runId;
    }

    @Transactional
    public void moduleFinished(Lease lease, UUID runId, String module, String status, String errorCode) {
        requireLease(lease);
        int count = jdbc.update("""
            UPDATE public.garden_photo_module_runs
            SET status=?,finished_at=now(),error_code=?
            WHERE id=? AND request_id=? AND module_name=? AND status='RUNNING'
            """, status, errorCode, runId, lease.requestId(), module);
        if (count != 1) throw new IllegalStateException("Module run already completed");
        jdbc.update("""
            INSERT INTO public.garden_photo_request_history
              (request_id,module_name,status,event_code,error_code)
            VALUES (?,?,?,?,?)
            """, lease.requestId(), module, status, module + "_" + status, errorCode);
    }

    @Transactional
    public void photoTransition(Lease lease, UUID photoId, String status, String event) {
        requireLease(lease);
        int count = jdbc.update("""
            UPDATE public.garden_photos SET workflow_status=?,updated_at=now()
            WHERE id=? AND EXISTS (
              SELECT 1 FROM public.garden_photo_requests
              WHERE request_id=? AND photo_id=?)
            """, status, photoId, lease.requestId(), photoId);
        if (count != 1) throw new IllegalStateException("Photo not linked to request");
        jdbc.update("""
            INSERT INTO public.garden_photo_status_history
              (photo_id,photo_status,processing_status,workflow_status,details)
            SELECT id,photo_status,processing_status,?,? FROM public.garden_photos WHERE id=?
            """, status, event, photoId);
    }

    @Transactional
    public void saveVision(Lease lease, UUID photoId, String json) {
        requireLease(lease);
        int count = jdbc.update("""
            UPDATE public.garden_photos
            SET analysis_provider='external-vision',analysis_json=CAST(? AS jsonb),
                vision_completed_at=now(),updated_at=now()
            WHERE id=? AND EXISTS (
              SELECT 1 FROM public.garden_photo_requests WHERE request_id=? AND photo_id=?)
            """, json, photoId, lease.requestId(), photoId);
        if (count != 1) throw new IllegalStateException("Photo not linked to request");
    }

    @Transactional
    public void requestTransition(Lease lease, String to, String event, String errorCode) {
        requireLease(lease);
        int count = jdbc.update("""
            UPDATE public.garden_photo_requests SET status=?,updated_at=now(),
              finished_at=CASE WHEN ? IN ('COMPLETED','FAILED','REJECTED') THEN now() ELSE finished_at END,
              lease_owner=CASE WHEN ? IN ('COMPLETED','FAILED','REJECTED') THEN NULL ELSE lease_owner END,
              lease_until=CASE WHEN ? IN ('COMPLETED','FAILED','REJECTED') THEN NULL ELSE lease_until END
            WHERE request_id=? AND status='RUNNING'
            """, to, to, to, to, lease.requestId());
        if (count != 1) throw new LeaseLostException(lease.requestId());
        jdbc.update("""
            INSERT INTO public.garden_photo_request_history
              (request_id,previous_status,status,event_code,error_code)
            VALUES (?,'RUNNING',?,?,?)
            """, lease.requestId(), to, event, errorCode);
    }
}
