package com.gardnaize.backend.service;

import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;

/** Expiry and its audit event commit or roll back together. */
@Service
public class PhotoLeaseReconciliationService {
    private static final Logger log = LoggerFactory.getLogger(PhotoLeaseReconciliationService.class);
    private final JdbcTemplate jdbc;
    private final TransactionTemplate transactions;

    public PhotoLeaseReconciliationService(JdbcTemplate jdbc, TransactionTemplate transactions) {
        this.jdbc = jdbc;
        this.transactions = transactions;
    }

    public int reconcileExpired() {
        return reconcileExpired(() -> {});
    }

    // Package-private failure injection for the PostgreSQL rollback integration test.
    int reconcileExpired(Runnable afterStatusUpdate) {
        Integer count = transactions.execute(status -> {
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
            afterStatusUpdate.run();
            for (UUID requestId : expired) {
                jdbc.update("""
                    INSERT INTO public.garden_photo_request_history
                        (request_id,previous_status,status,event_code,error_code)
                    VALUES (?,'RUNNING','RECONCILIATION_REQUIRED',
                            'LEASE_EXPIRED','RECOVERY_REVIEW_REQUIRED')
                    """, requestId);
            }
            return expired.size();
        });
        if (count != null && count > 0) {
            log.warn("event=LEASE_EXPIRED count={} status=RECONCILIATION_REQUIRED", count);
        }
        return count == null ? 0 : count;
    }
}
