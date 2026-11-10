package com.gardnaize.photo;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "garden_photo_submission", schema = "public")
public class PhotoSubmission {
    @Id
    private UUID id;
    @Column(nullable = false, length = 2000)
    private String description;
    @Column(nullable = false, length = 100)
    private String contentType;
    @Column(nullable = false)
    private String filename;
    @Column(nullable = false)
    private byte[] image;
    @Column(nullable = false, length = 32)
    private String status;
    @Column(columnDefinition = "text")
    private String visionJson;
    @Column(nullable = false)
    private Instant createdAt;

    protected PhotoSubmission() {}

    public PhotoSubmission(UUID id, String description, String contentType, String filename, byte[] image) {
        this.id = id;
        this.description = description;
        this.contentType = contentType;
        this.filename = filename;
        this.image = image;
        this.status = "VALIDATED";
        this.createdAt = Instant.now();
    }

    public UUID getId() { return id; }
    public String getStatus() { return status; }
    public String getVisionJson() { return visionJson; }
    public void markVisionComplete(String json) { this.visionJson = json; this.status = "VISION_COMPLETED"; }
    public void markVisionFailed() { this.status = "VISION_FAILED"; }
}
