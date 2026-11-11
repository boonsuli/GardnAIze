package com.gardnaize.backend.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.server.ResponseStatusException;

import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class GardenPhotoServiceTest {
    private final JdbcTemplate jdbc = mock(JdbcTemplate.class);
    private final GardenPhotoService service = new GardenPhotoService(
            jdbc, new ObjectMapper(), "http://localhost:9000", "test", "", false);

    private static final String ANSWERS = """
        {"exposure":"FULL_SUN","waterAvailability":"MODERATE",
         "maintenancePreference":"LOW"}
        """;

    @Test
    void consentIsMandatoryBeforeAnyDatabaseOrVisionActivity() {
        UUID gardenId = UUID.randomUUID();
        var photo = new MockMultipartFile("file", "garden.jpg", "image/jpeg", new byte[] {1});
        var error = assertThrows(ResponseStatusException.class, () ->
                service.upload(gardenId, photo, "Garden", ANSWERS, null));
        assertEquals(403, error.getStatusCode().value());
        verifyNoInteractions(jdbc);
    }

    @Test
    void incorrectConsentKeyIsRejectedBeforePersistence() {
        UUID gardenId = UUID.randomUUID();
        var photo = new MockMultipartFile("file", "garden.jpg", "image/jpeg", new byte[] {1});
        var error = assertThrows(ResponseStatusException.class, () ->
                service.upload(gardenId, photo, "Garden", ANSWERS, "privacy.otherNotice"));
        assertEquals(403, error.getStatusCode().value());
        verifyNoInteractions(jdbc);
    }

    @Test
    void invalidQuestionnaireJsonIsRejectedBeforePersistence() {
        UUID gardenId = UUID.randomUUID();
        var photo = new MockMultipartFile("file", "garden.jpg", "image/jpeg", new byte[] {1});
        var error = assertThrows(ResponseStatusException.class, () ->
                service.upload(gardenId, photo, "Garden", "{bad json",
                        "privacy.externalProcessingNotice"));
        assertEquals(400, error.getStatusCode().value());
        verifyNoInteractions(jdbc);
    }

    @Test
    void missingRequiredAnswersAreRejectedBeforePersistence() {
        UUID gardenId = UUID.randomUUID();
        var photo = new MockMultipartFile("file", "garden.jpg", "image/jpeg", new byte[] {1});
        var error = assertThrows(ResponseStatusException.class, () ->
                service.upload(gardenId, photo, "Garden", "{\\"exposure\\":\\"FULL_SUN\\"}",
                        "privacy.externalProcessingNotice"));
        assertEquals(400, error.getStatusCode().value());
        verifyNoInteractions(jdbc);
    }

    @Test
    void unknownGardenIsRejected() {
        UUID gardenId = UUID.randomUUID();
        when(jdbc.queryForObject(any(String.class), eq(Boolean.class), eq(gardenId)))
                .thenReturn(false);
        assertThrows(ResponseStatusException.class, () ->
                service.upload(gardenId, new MockMultipartFile(
                        "file", "garden.jpg", "image/jpeg", new byte[] {1, 2, 3})));
    }

    @Test
    void oversizedPhotoIsRejected() {
        UUID gardenId = UUID.randomUUID();
        when(jdbc.queryForObject(any(String.class), eq(Boolean.class), eq(gardenId)))
                .thenReturn(true);
        byte[] oversized = new byte[5 * 1024 * 1024 + 1];
        assertThrows(ResponseStatusException.class, () ->
                service.upload(gardenId, new MockMultipartFile(
                        "file", "garden.jpg", "image/jpeg", oversized), "Garden"));
    }

    @Test
    void overlongDescriptionIsRejected() {
        UUID gardenId = UUID.randomUUID();
        when(jdbc.queryForObject(any(String.class), eq(Boolean.class), eq(gardenId)))
                .thenReturn(true);
        assertThrows(ResponseStatusException.class, () ->
                service.upload(gardenId, new MockMultipartFile(
                        "file", "garden.jpg", "image/jpeg", new byte[] {1}), "a".repeat(1001)));
    }

    @Test
    void invalidMediaTypeIsRejected() {
        UUID gardenId = UUID.randomUUID();
        when(jdbc.queryForObject(any(String.class), eq(Boolean.class), eq(gardenId)))
                .thenReturn(true);
        assertThrows(ResponseStatusException.class, () ->
                service.upload(gardenId, new MockMultipartFile(
                        "file", "garden.gif", "image/gif", new byte[] {1, 2, 3})));
    }
}
