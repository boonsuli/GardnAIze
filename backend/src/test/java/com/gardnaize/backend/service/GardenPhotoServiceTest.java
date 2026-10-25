package com.gardnaize.backend.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.server.ResponseStatusException;

import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class GardenPhotoServiceTest {
    private final JdbcTemplate jdbc = mock(JdbcTemplate.class);
    private final GardenPhotoService service = new GardenPhotoService(
            jdbc, new ObjectMapper(), "http://localhost:9000", "test", "", false);

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
    void invalidMediaTypeIsRejected() {
        UUID gardenId = UUID.randomUUID();
        when(jdbc.queryForObject(any(String.class), eq(Boolean.class), eq(gardenId)))
                .thenReturn(true);
        assertThrows(ResponseStatusException.class, () ->
                service.upload(gardenId, new MockMultipartFile(
                        "file", "garden.gif", "image/gif", new byte[] {1, 2, 3})));
    }
}
