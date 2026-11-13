package com.gardnaize.backend.service;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.server.ResponseStatusException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.gardnaize.backend.api.PhotoAnalysisResponse;

class PhotoProcessingRequestServiceTest {
    private final GardenPhotoService photos = mock(GardenPhotoService.class);
    private final JdbcTemplate jdbc = mock(JdbcTemplate.class);
    private final PhotoProcessingRequestService service =
            new PhotoProcessingRequestService(photos, jdbc, new ObjectMapper());
    private final MockMultipartFile photo = new MockMultipartFile(
            "file", "garden.png", "image/png", new byte[] {1});

    @Test
    void refusesMissingConsentWithoutPersistence() {
        var error = assertThrows(ResponseStatusException.class,
                () -> service.accept(UUID.randomUUID(), photo, "", "{}", null));
        assertEquals(HttpStatus.FORBIDDEN, error.getStatusCode());
        verifyNoInteractions(jdbc, photos);
    }

    @Test
    void refusesMissingRequiredAnswersWithoutPersistence() {
        var error = assertThrows(ResponseStatusException.class,
                () -> service.accept(UUID.randomUUID(), photo, "", "{}",
                        "privacy.externalProcessingNotice"));
        assertEquals(HttpStatus.BAD_REQUEST, error.getStatusCode());
        verifyNoInteractions(jdbc, photos);
    }

    @Test
    void createsPersistentRequestAndAuditEvent() {
        UUID gardenId = UUID.randomUUID();
        UUID photoId = UUID.randomUUID();
        when(photos.upload(gardenId, photo, "test")).thenReturn(
                new PhotoAnalysisResponse(photoId, gardenId, "CHECKED", "IN_PROGRESS", null, null));
        var accepted = service.accept(gardenId, photo, "test",
                "{\"exposure\":\"FULL_SUN\",\"waterAvailability\":\"LOW\",\"maintenancePreference\":\"LOW\"}",
                "privacy.externalProcessingNotice");
        assertNotNull(accepted.requestId());
        assertEquals(photoId, accepted.photoId());
        assertEquals("ACCEPTED", accepted.status());
        assertTrue(accepted.statusUrl().endsWith(accepted.requestId().toString()));
        verify(jdbc, times(3)).update(anyString(), any(Object[].class));
    }
}
