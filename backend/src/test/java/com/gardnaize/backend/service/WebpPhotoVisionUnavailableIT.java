package com.gardnaize.backend.service;

import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.util.UUID;
import javax.imageio.ImageIO;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.server.ResponseStatusException;

import static org.junit.jupiter.api.Assertions.*;

/** PostgreSQL integration test: a disabled external provider must not discard an uploaded photo. */
@SpringBootTest(properties = "gardnaize.vision.enabled=false")
class WebpPhotoVisionUnavailableIT {
    @Autowired JdbcTemplate jdbc;
    @Autowired GardenPhotoService photoService;

    @Test
    void consentedUploadReturns503ButPersistsWebpWhenVisionIsDisabled() throws Exception {
        UUID gardenId = UUID.randomUUID();
        jdbc.update(
            "INSERT INTO garden_projects(id,name,location,exposure,soil_type,created_at) VALUES (?,?,?,?,?,now())",
            gardenId, "Vision unavailable integration garden", "Paris", "FULL_SUN", "LOAMY");
        try {
            BufferedImage image = new BufferedImage(640, 480, BufferedImage.TYPE_INT_RGB);
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            assertTrue(ImageIO.write(image, "png", output));
            MockMultipartFile file = new MockMultipartFile(
                "file", "garden.png", "image/png", output.toByteArray());

            String answersJson = """
                {
                  "exposure": "FULL_SUN",
                  "waterAvailability": "MODERATE",
                  "maintenancePreference": "LOW"
                }
                """;

            ResponseStatusException exception = assertThrows(
                ResponseStatusException.class,
                () -> photoService.upload(
                    gardenId, file, "Consented test photo", answersJson,
                    "privacy.externalProcessingNotice"));
            assertEquals(HttpStatus.SERVICE_UNAVAILABLE, exception.getStatusCode());

            String mime = jdbc.queryForObject(
                "SELECT content_type FROM garden_photos WHERE garden_id=?",
                String.class, gardenId);
            byte[] bytes = jdbc.queryForObject(
                "SELECT image_bytes FROM garden_photos WHERE garden_id=?",
                byte[].class, gardenId);
            String photoStatus = jdbc.queryForObject(
                "SELECT photo_status FROM garden_photos WHERE garden_id=?",
                String.class, gardenId);
            String processingStatus = jdbc.queryForObject(
                "SELECT processing_status FROM garden_photos WHERE garden_id=?",
                String.class, gardenId);
            Integer questionnaireCount = jdbc.queryForObject(
                """
                SELECT count(*) FROM garden_photo_questionnaire q
                JOIN garden_photos p ON p.id=q.photo_id
                WHERE p.garden_id=?
                """, Integer.class, gardenId);

            assertEquals("image/webp", mime);
            assertNotNull(bytes);
            assertTrue(bytes.length >= 12);
            assertEquals("RIFF", new String(bytes, 0, 4, java.nio.charset.StandardCharsets.US_ASCII));
            assertEquals("WEBP", new String(bytes, 8, 4, java.nio.charset.StandardCharsets.US_ASCII));
            BufferedImage decoded = ImageIO.read(new java.io.ByteArrayInputStream(bytes));
            assertNotNull(decoded);
            assertEquals(640, decoded.getWidth());
            assertEquals(480, decoded.getHeight());
            assertEquals("TRANSFER_FAILED", photoStatus);
            assertEquals("FAILED", processingStatus);
            assertEquals(1, questionnaireCount);
        } finally {
            jdbc.update("DELETE FROM garden_projects WHERE id=?", gardenId);
        }
    }
}
