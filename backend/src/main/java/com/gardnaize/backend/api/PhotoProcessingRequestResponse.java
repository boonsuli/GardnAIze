package com.gardnaize.backend.api;

import java.time.OffsetDateTime;
import java.util.UUID;

public record PhotoProcessingRequestResponse(
        UUID requestId,
        UUID gardenId,
        UUID photoId,
        String status,
        OffsetDateTime createdAt,
        String statusUrl
) {}
