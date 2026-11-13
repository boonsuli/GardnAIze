package com.gardnaize.backend.service;

import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Transactional state transitions and append-only audit for a single processing request. */
@Service
public class PhotoWorkflowStateService {
    private static final Logger log = LoggerFactory.getLogger(PhotoWorkflowStateService.class);
    private final JdbcTemplate jdbc;

    public PhotoWorkflowStateService(JdbcTemplate jdbc) { this.jdbc = jdbc; }

    @Transactional
    public void requestTransition(UUID requestId, String from, String to, String event, String errorCode) {
        int updated = jdbc.update("""
            UPDATE public.garden_photo_requests SET status=?, updated_at=now(),
                finished_at=CASE WHEN ? IN ('COMPLETED','FAILED','REJECTED') THEN now() ELSE finished_at END,
                lease_owner=CASE WHEN ? IN ('COMPLETED','FAILED','REJECTED') THEN NULL ELSE lease_owner END,
                lease_until=CASE WHEN ? IN ('COMPLETED','FAILED','REJECTED') THEN NULL ELSE lease_until END
            WHERE request_id=? AND status=?
            """, to, to, to, to, requestId, from);
        if (updated != 1) throw new IllegalStateException("Concurrent request transition: " + requestId);
        jdbc.update("""
            INSERT INTO public.garden_photo_request_history
                (request_id,previous_status,status,event_code,error_code)
            VALUES (?,?,?,?,?)
            """, requestId, from, to, event, errorCode);
        log.info("event={} requestId={} previousStatus={} status={} errorCode={}",
                event, requestId, from, to, errorCode);
    }

    @Transactional
    public UUID moduleStarted(UUID requestId, String module) {
        UUID runId = UUID.randomUUID();
        jdbc.update("""
            INSERT INTO public.garden_photo_module_runs
                (id,request_id,module_name,status,attempt_number,started_at)
            VALUES (?,?,?,'RUNNING',
                (SELECT COALESCE(MAX(attempt_number),0)+1 FROM public.garden_photo_module_runs
                 WHERE request_id=? AND module_name=?),now())
            """, runId, requestId, module, requestId, module);
        jdbc.update("""
            INSERT INTO public.garden_photo_request_history (request_id,module_name,status,event_code)
            VALUES (?,?,'RUNNING',?)
            """, requestId, module, module + "_STARTED");
        log.info("event=MODULE_STARTED requestId={} module={} runId={}", requestId, module, runId);
        return runId;
    }

    @Transactional
    public void moduleFinished(UUID requestId, UUID runId, String module, String status, String errorCode) {
        int updated = jdbc.update("""
            UPDATE public.garden_photo_module_runs SET status=?,finished_at=now(),error_code=?
            WHERE id=? AND request_id=? AND status='RUNNING'
            """, status, errorCode, runId, requestId);
        if (updated != 1) throw new IllegalStateException("Module run no longer active: " + runId);
        jdbc.update("""
            INSERT INTO public.garden_photo_request_history (request_id,module_name,status,event_code,error_code)
            VALUES (?,?,?,?,?)
            """, requestId, module, status, module + "_" + status, errorCode);
        log.info("event=MODULE_FINISHED requestId={} module={} status={} errorCode={}",
                requestId, module, status, errorCode);
    }

    @Transactional
    public void photoTransition(UUID photoId, String status, String event) {
        jdbc.update("""
            UPDATE public.garden_photos SET workflow_status=?,updated_at=now() WHERE id=?
            """, status, photoId);
        jdbc.update("""
            INSERT INTO public.garden_photo_status_history
                (photo_id,photo_status,processing_status,workflow_status,details)
            SELECT id,photo_status,processing_status,?,? FROM public.garden_photos WHERE id=?
            """, status, event, photoId);
        log.info("event={} photoId={} workflowStatus={}", event, photoId, status);
    }
}
