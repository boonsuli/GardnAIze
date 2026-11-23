package com.gardnaize.backend.service;

import java.time.Duration;
import java.time.Instant;
import java.util.Objects;
import org.springframework.stereotype.Component;

/**
 * Decision gate for the new VISION/questionnaire -> PLANT worker.
 *
 * <p>This component deliberately does not dispatch external calls or mutate workflow
 * status. The existing master owns leases; the eventual worker must use
 * PhotoWorkflowFencingService for all persistent writes. This gate is safe to
 * integrate incrementally while the GDAI-PLANT FastAPI contract is finalized.
 */
@Component
public class VisionPlantWorkflowWorker {

    public enum Decision {
        WAIT_FOR_VISION,
        WAIT_FOR_QUESTIONNAIRE,
        WAIT_FOR_CONTEXT_QUESTION,
        READY_FOR_PLANT,
        VISION_UNAVAILABLE
    }

    /**
     * @param visionFinished true when the VISION module has reached a terminal result
     * @param visionUsable true only when VISION produced valid, analyzable garden data
     * @param questionnaireComplete true only when all mandatory answers and consents are recorded
     * @param contextQuestionRequired true when one contextual question was selected
     * @param contextQuestionAnswered true when the selected question has been answered
     * @param contextDeadline optional deadline after which the contextual question is skipped
     * @param now current time, supplied by the caller for deterministic testing
     */
    public Decision evaluate(boolean visionFinished, boolean visionUsable,
            boolean questionnaireComplete, boolean contextQuestionRequired,
            boolean contextQuestionAnswered, Instant contextDeadline, Instant now) {
        Objects.requireNonNull(now, "now");
        if (!visionFinished) return Decision.WAIT_FOR_VISION;
        if (!visionUsable) return Decision.VISION_UNAVAILABLE;
        if (!questionnaireComplete) return Decision.WAIT_FOR_QUESTIONNAIRE;
        if (contextQuestionRequired && !contextQuestionAnswered
                && (contextDeadline == null || now.isBefore(contextDeadline))) {
            return Decision.WAIT_FOR_CONTEXT_QUESTION;
        }
        return Decision.READY_FOR_PLANT;
    }

    /**
     * Suggested default deadline for an optional context question.
     * It is NOT a timeout for VISION or for mandatory consent.
     */
    public Instant contextDeadline(Instant publishedAt, Duration maximumWait) {
        Objects.requireNonNull(publishedAt, "publishedAt");
        Objects.requireNonNull(maximumWait, "maximumWait");
        if (maximumWait.isNegative()) throw new IllegalArgumentException("maximumWait must be >= 0");
        return publishedAt.plus(maximumWait);
    }
}
