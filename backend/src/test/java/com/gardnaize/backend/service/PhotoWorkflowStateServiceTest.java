package com.gardnaize.backend.service;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;

class PhotoWorkflowStateServiceTest {
    private final JdbcTemplate jdbc = mock(JdbcTemplate.class);
    private final PhotoWorkflowStateService states = new PhotoWorkflowStateService(jdbc);

    @Test
    void requestTransitionRejectsStaleStateWithoutWritingHistory() {
        UUID requestId = UUID.randomUUID();
        when(jdbc.update(anyString(), any(Object[].class))).thenReturn(0);
        assertThrows(IllegalStateException.class, () ->
                states.requestTransition(requestId, "RUNNING", "COMPLETED",
                        "WORKFLOW_COMPLETED", null));
        verify(jdbc, times(1)).update(anyString(), any(Object[].class));
    }

    @Test
    void moduleStartedReturnsUniqueRunId() {
        UUID requestId = UUID.randomUUID();
        UUID first = states.moduleStarted(requestId, "VALID");
        UUID second = states.moduleStarted(requestId, "VISION");
        assertNotEquals(first, second);
        verify(jdbc, times(4)).update(anyString(), any(Object[].class));
    }
}
