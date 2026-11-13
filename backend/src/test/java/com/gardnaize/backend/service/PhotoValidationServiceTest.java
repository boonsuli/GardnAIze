package com.gardnaize.backend.service;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.http.HttpStatus;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.client.RestClient;
import org.springframework.web.server.ResponseStatusException;

class PhotoValidationServiceTest {
    @Test
    void forwardsMultipartPhotoToRealValidationEndpoint() {
        RestClient client = mock(RestClient.class);
        RestClient.RequestBodyUriSpec request = mock(RestClient.RequestBodyUriSpec.class, Mockito.RETURNS_SELF);
        RestClient.ResponseSpec response = mock(RestClient.ResponseSpec.class);
        when(client.post()).thenReturn(request);
        when(request.retrieve()).thenReturn(response);
        when(response.body(Map.class)).thenReturn(Map.of(
                "valid", true, "status", "VALID", "confidence", 0.94,
                "predicted_class", "garden", "message", "Accepted"));
        var photo = new MockMultipartFile("file", "garden.png", "image/png", new byte[] {1, 2, 3});
        Map<String, Object> result = new PhotoValidationService(client).validate(photo);
        assertEquals(true, result.get("valid"));
        assertEquals("VALID", result.get("status"));
        verify(request).uri("/api/v1/validation/photo");
    }

    @Test
    void asyncValidationReturnsFutureAndUsesConfiguredExecutor() {
        RestClient client = mock(RestClient.class);
        RestClient.RequestBodyUriSpec request = mock(RestClient.RequestBodyUriSpec.class, Mockito.RETURNS_SELF);
        RestClient.ResponseSpec response = mock(RestClient.ResponseSpec.class);
        when(client.post()).thenReturn(request);
        when(request.retrieve()).thenReturn(response);
        when(response.body(Map.class)).thenReturn(Map.of(
                "valid", true, "status", "VALID", "confidence", 0.98));
        var service = new PhotoValidationService(client);
        java.util.concurrent.atomic.AtomicBoolean scheduled = new java.util.concurrent.atomic.AtomicBoolean();
        service.setValidationExecutor(command -> {
            scheduled.set(true);
            command.run();
        });
        var photo = new MockMultipartFile("file", "garden.png", "image/png", new byte[] {1, 2});
        var result = service.validateAsync(photo);
        assertTrue(scheduled.get());
        assertEquals("VALID", result.join().get("status"));
    }

    @Test
    void rejectsUnsupportedMimeBeforeCallingValidator() {
        RestClient client = mock(RestClient.class);
        var photo = new MockMultipartFile("file", "bad.txt", "text/plain", new byte[] {1});
        ResponseStatusException ex = assertThrows(ResponseStatusException.class,
                () -> new PhotoValidationService(client).validate(photo));
        assertEquals(HttpStatus.UNSUPPORTED_MEDIA_TYPE, ex.getStatusCode());
        verifyNoInteractions(client);
    }

    @Test
    void failsClosedOnMalformedValidationResponse() {
        RestClient client = mock(RestClient.class);
        RestClient.RequestBodyUriSpec request = mock(RestClient.RequestBodyUriSpec.class, Mockito.RETURNS_SELF);
        RestClient.ResponseSpec response = mock(RestClient.ResponseSpec.class);
        when(client.post()).thenReturn(request);
        when(request.retrieve()).thenReturn(response);
        when(response.body(Map.class)).thenReturn(Map.of("valid", true));
        var photo = new MockMultipartFile("file", "garden.jpg", "image/jpeg", new byte[] {1});
        ResponseStatusException ex = assertThrows(ResponseStatusException.class,
                () -> new PhotoValidationService(client).validate(photo));
        assertEquals(HttpStatus.BAD_GATEWAY, ex.getStatusCode());
    }
}
