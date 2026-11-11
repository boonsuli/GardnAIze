package com.gardnaize.backend.service;

import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.Iterator;
import javax.imageio.IIOImage;
import javax.imageio.ImageIO;
import javax.imageio.ImageWriteParam;
import javax.imageio.ImageWriter;
import javax.imageio.stream.ImageOutputStream;
import org.springframework.stereotype.Component;

/** Converts uploaded JPEG/PNG/WebP to a canonical WebP blob. */
@Component
public class WebpImageCodec {
    private static final int MAX_PIXELS = 24_000_000;

    public record Encoded(byte[] bytes, int width, int height) {}

    public Encoded normalize(byte[] original) throws IOException {
        BufferedImage image = ImageIO.read(new ByteArrayInputStream(original));
        if (image == null) {
            throw new IOException("Unsupported or corrupt image");
        }
        long pixels = (long) image.getWidth() * image.getHeight();
        if (pixels < 1 || pixels > MAX_PIXELS) {
            throw new IOException("Image dimensions exceed limit");
        }
        Iterator<ImageWriter> writers = ImageIO.getImageWritersByMIMEType("image/webp");
        if (!writers.hasNext()) {
            throw new IOException("WebP ImageIO writer unavailable");
        }
        ImageWriter writer = writers.next();
        try (ByteArrayOutputStream output = new ByteArrayOutputStream();
             ImageOutputStream stream = ImageIO.createImageOutputStream(output)) {
            writer.setOutput(stream);
            ImageWriteParam params = writer.getDefaultWriteParam();
            if (params.canWriteCompressed()) {
                params.setCompressionMode(ImageWriteParam.MODE_EXPLICIT);
                String[] types = params.getCompressionTypes();
                if (types != null && types.length > 0) {
                    String selected = java.util.Arrays.stream(types)
                        .filter(t -> t.equalsIgnoreCase("Lossy") || t.equalsIgnoreCase("Lossy Compression"))
                        .findFirst().orElse(types[0]);
                    params.setCompressionType(selected);
                    if (!selected.toLowerCase(java.util.Locale.ROOT).contains("lossless")) {
                        params.setCompressionQuality(0.9f);
                    }
                }
            }
            writer.write(null, new IIOImage(image, null, null), params);
            stream.flush();
            byte[] webp = output.toByteArray();
            if (webp.length < 12 || webp[0] != 'R' || webp[1] != 'I'
                    || webp[2] != 'F' || webp[3] != 'F'
                    || webp[8] != 'W' || webp[9] != 'E'
                    || webp[10] != 'B' || webp[11] != 'P') {
                throw new IOException("Writer did not produce WebP");
            }
            return new Encoded(webp, image.getWidth(), image.getHeight());
        } finally {
            writer.dispose();
        }
    }
}
