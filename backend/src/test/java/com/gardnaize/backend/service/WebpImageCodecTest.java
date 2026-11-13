package com.gardnaize.backend.service;

import java.awt.Color;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import javax.imageio.ImageIO;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class WebpImageCodecTest {
    private final WebpImageCodec codec = new WebpImageCodec();

    private byte[] image(String format) throws IOException {
        BufferedImage image = new BufferedImage(640, 480, BufferedImage.TYPE_INT_RGB);
        image.setRGB(10, 10, Color.GREEN.getRGB());
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        assertTrue(ImageIO.write(image, format, output));
        return output.toByteArray();
    }

    @Test
    void jpegIsNormalizedToWebp() throws Exception {
        var result = codec.normalize(image("jpeg"));
        assertEquals(640, result.width());
        assertEquals(480, result.height());
        assertEquals("RIFF", new String(result.bytes(), 0, 4, java.nio.charset.StandardCharsets.US_ASCII));
        assertEquals("WEBP", new String(result.bytes(), 8, 4, java.nio.charset.StandardCharsets.US_ASCII));
        assertNotNull(ImageIO.read(new java.io.ByteArrayInputStream(result.bytes())));
    }

    @Test
    void pngIsNormalizedToWebp() throws Exception {
        var result = codec.normalize(image("png"));
        assertTrue(result.bytes().length > 12);
        assertEquals("WEBP", new String(result.bytes(), 8, 4, java.nio.charset.StandardCharsets.US_ASCII));
    }

    @Test
    void webpRoundTripIsSupported() throws Exception {
        byte[] first = codec.normalize(image("png")).bytes();
        byte[] second = codec.normalize(first).bytes();
        assertEquals("WEBP", new String(second, 8, 4, java.nio.charset.StandardCharsets.US_ASCII));
    }

    @Test
    void invalidImageIsRejected() {
        assertThrows(IOException.class, () -> codec.normalize(new byte[]{1,2,3,4}));
    }
}
