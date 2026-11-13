package com.gardnaize.backend.service;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpServer;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import javax.imageio.ImageIO;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

/**
 * PostgreSQL + real async worker + local HTTP stubs. Never contacts Gemini.
 * CI needs PostgreSQL and Flyway migrations.
 */
@SpringBootTest(properties = {
    "gardnaize.vision.enabled=true",
    "gardnaize.workflow.poll-ms=3600000",
    "gardnaize.vision.api-key="
})
class PhotoWorkflowWorkerIT {
    private static HttpServer validServer;
    private static HttpServer visionServer;
    private static final AtomicInteger validCalls = new AtomicInteger();
    private static final AtomicInteger visionCalls = new AtomicInteger();
    private static volatile boolean valid = true;
    private static volatile boolean visionFailure = false;

    @DynamicPropertySource
    static void configure(DynamicPropertyRegistry registry) {
        startServers();
        registry.add("gardnaize.validation.base-url", () -> "http://127.0.0.1:" + validServer.getAddress().getPort());
        registry.add("gardnaize.vision.base-url", () -> "http://127.0.0.1:" + visionServer.getAddress().getPort());
    }

    private static synchronized void startServers() {
        if (validServer != null) return;
        try {
            validServer = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
            validServer.createContext("/api/v1/validation/photo", exchange -> {
                validCalls.incrementAndGet();
                byte[] response = ("{\"valid\":" + valid + ",\"status\":\""
                        + (valid ? "VALID" : "INVALID") + "\",\"confidence\":0.95}")
                        .getBytes(StandardCharsets.UTF_8);
                exchange.getResponseHeaders().set("Content-Type", "application/json");
                exchange.sendResponseHeaders(200, response.length);
                try (var output = exchange.getResponseBody()) { output.write(response); }
            });
            validServer.start();
            visionServer = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
            visionServer.createContext("/analyze", exchange -> {
                visionCalls.incrementAndGet();
                boolean fail = visionFailure;
                byte[] response = (fail ? "{\"error\":\"unavailable\"}" :
                        "{\"isGarden\":true,\"isAnalyzable\":true,\"description\":{}}")
                        .getBytes(StandardCharsets.UTF_8);
                exchange.getResponseHeaders().set("Content-Type", "application/json");
                exchange.sendResponseHeaders(fail ? 503 : 200, response.length);
                try (var output = exchange.getResponseBody()) { output.write(response); }
            });
            visionServer.start();
        } catch (Exception ex) {
            throw new IllegalStateException(ex);
        }
    }

    @AfterAll
    static void stopServers() {
        if (validServer != null) validServer.stop(0);
        if (visionServer != null) visionServer.stop(0);
    }

    @Autowired JdbcTemplate jdbc;
    @Autowired PhotoWorkflowWorker worker;
    @Autowired PhotoProcessingRequestService requests;
    @Autowired PhotoWorkflowStateService states;

    private record Fixture(UUID gardenId, UUID photoId, UUID requestId) {}

    private Fixture create() throws Exception {
        UUID gardenId = UUID.randomUUID();
        jdbc.update("INSERT INTO garden_projects(id,name,location,exposure,soil_type,created_at) VALUES (?,?,?,?,?,now())",
                gardenId, "Workflow integration", "Paris", "FULL_SUN", "LOAMY");
        var image = new BufferedImage(640, 480, BufferedImage.TYPE_INT_RGB);
        var bytes = new ByteArrayOutputStream();
        assertTrue(ImageIO.write(image, "png", bytes));
        var photo = new MockMultipartFile("file", "garden.png", "image/png", bytes.toByteArray());
        var accepted = requests.accept(gardenId, photo, "Test",
                "{\"exposure\":\"FULL_SUN\",\"waterAvailability\":\"LOW\",\"maintenancePreference\":\"LOW\"}",
                "privacy.externalProcessingNotice");
        assertEquals("ACCEPTED", accepted.status());
        states.requestTransition(accepted.requestId(), "ACCEPTED", "RUNNING", "TEST_CLAIMED", null);
        return new Fixture(gardenId, accepted.photoId(), accepted.requestId());
    }

    private String status(UUID requestId) {
        return jdbc.queryForObject("SELECT status FROM garden_photo_requests WHERE request_id=?",
                String.class, requestId);
    }

    @Test
    void validPhotoAdvancesToVisionAndCompletes() throws Exception {
        valid = true;
        visionFailure = false;
        int before = visionCalls.get();
        Fixture f = create();
        try {
            worker.execute(f.requestId(), f.photoId()).get(15, TimeUnit.SECONDS);
            assertEquals("COMPLETED", status(f.requestId()));
            assertEquals("VISION_COMPLETED", jdbc.queryForObject(
                    "SELECT workflow_status FROM garden_photos WHERE id=?", String.class, f.photoId()));
            assertEquals(before + 1, visionCalls.get());
            assertEquals(2, jdbc.queryForObject(
                    "SELECT count(*) FROM garden_photo_module_runs WHERE request_id=? AND status='COMPLETED'",
                    Integer.class, f.requestId()));
            assertTrue(jdbc.queryForObject(
                    "SELECT count(*) FROM garden_photo_request_history WHERE request_id=? AND event_code='WORKFLOW_COMPLETED'",
                    Integer.class, f.requestId()) > 0);
        } finally {
            jdbc.update("DELETE FROM garden_projects WHERE id=?", f.gardenId());
        }
    }

    @Test
    void rejectedPhotoNeverCallsVision() throws Exception {
        valid = false;
        int before = visionCalls.get();
        Fixture f = create();
        try {
            worker.execute(f.requestId(), f.photoId()).get(15, TimeUnit.SECONDS);
            assertEquals("REJECTED", status(f.requestId()));
            assertEquals(before, visionCalls.get());
            assertEquals(0, jdbc.queryForObject(
                    "SELECT count(*) FROM garden_photo_module_runs WHERE request_id=? AND module_name='VISION'",
                    Integer.class, f.requestId()));
        } finally {
            valid = true;
            jdbc.update("DELETE FROM garden_projects WHERE id=?", f.gardenId());
        }
    }

    @Test
    void providerUnavailableIsPersistedAsFailure() throws Exception {
        valid = true;
        visionFailure = true;
        Fixture f = create();
        try {
            worker.execute(f.requestId(), f.photoId()).get(15, TimeUnit.SECONDS);
            assertEquals("FAILED", status(f.requestId()));
            assertEquals("FAILED", jdbc.queryForObject(
                    "SELECT status FROM garden_photo_module_runs WHERE request_id=? AND module_name='VISION'",
                    String.class, f.requestId()));
        } finally {
            visionFailure = false;
            jdbc.update("DELETE FROM garden_projects WHERE id=?", f.gardenId());
        }
    }
}
