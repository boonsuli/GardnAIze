package com.gardnaize.backend.service;

import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.util.UUID;
import javax.imageio.ImageIO;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.context.TestPropertySource;
import org.springframework.web.server.ResponseStatusException;
import static org.junit.jupiter.api.Assertions.*;

/** Runs against the PostgreSQL service started by GitHub Actions. */
@SpringBootTest(properties = "gardnaize.vision.enabled=false")
class WebpPhotoPersistenceIT {
    @Autowired JdbcTemplate jdbc;
    @Autowired GardenPhotoService photoService;

    @Test
    void uploadPersistsWebpEvenWhenExternalVisionIsUnavailable() throws Exception {
        UUID gardenId = UUID.randomUUID();
        jdbc.update("INSERT INTO garden_projects(id,name,location,exposure,soil_type) VALUES (?,?,?,?,?)",
            gardenId, "Integration garden", "Paris", "FULL_SUN", "LOAMY");
        try {
            BufferedImage image = new BufferedImage(640, 480, BufferedImage.TYPE_INT_RGB);
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            assertTrue(ImageIO.write(image, "png", output));
            MockMultipartFile file = new MockMultipartFile("file", "garden.png", "image/png", output.toByteArray());
            assertThrows(ResponseStatusException.class,
                () -> photoService.upload(gardenId, file, "Test photo"));
            String mime = jdbc.queryForObject(
                "SELECT content_type FROM garden_photos WHERE garden_id=?", String.class, gardenId);
            byte[] bytes = jdbc.queryForObject(
                "SELECT image_bytes FROM garden_photos WHERE garden_id=?", byte[].class, gardenId);
            assertEquals("image/webp", mime);
            assertNotNull(bytes);
            assertEquals("WEBP", new String(bytes, 8, 4, java.nio.charset.StandardCharsets.US_ASCII));
        } finally {
            jdbc.update("DELETE FROM garden_projects WHERE id=?", gardenId);
        }
    }
}
