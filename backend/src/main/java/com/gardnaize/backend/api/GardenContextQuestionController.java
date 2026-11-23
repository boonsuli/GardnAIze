package com.gardnaize.backend.api;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.gardnaize.backend.service.GardenContextQuestionSelector;
import io.swagger.v3.oas.annotations.Operation;
import java.util.Map;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

/**
 * Pollable contextual-question preview. This is a read-only endpoint: it does
 * not finalize questionnaire responses or dispatch PLANT.
 */
@RestController
@RequestMapping("/api/v1/gardens/{gardenId}/photo-requests/{requestId}/context-question")
public class GardenContextQuestionController {
    private final JdbcTemplate jdbc;
    private final ObjectMapper mapper;
    private final GardenContextQuestionSelector selector;

    public GardenContextQuestionController(JdbcTemplate jdbc, ObjectMapper mapper,
            GardenContextQuestionSelector selector) {
        this.jdbc = jdbc;
        this.mapper = mapper;
        this.selector = selector;
    }

    public record ContextQuestionResponse(String state, String questionKey, String reason) {}

    @GetMapping
    @Operation(summary = "Poll the optional contextual question derived from GDAI-VISION")
    public ContextQuestionResponse get(@PathVariable UUID gardenId, @PathVariable UUID requestId) {
        var rows = jdbc.query("""
            SELECT p.analysis_json::text AS vision_json, q.answers::text AS answers_json,
                   r.status AS request_status
            FROM public.garden_photo_requests r
            JOIN public.garden_photos p ON p.id=r.photo_id
            LEFT JOIN public.garden_photo_questionnaire q ON q.photo_id=p.id
            WHERE r.garden_id=? AND r.request_id=?
            """, (rs, i) -> Map.of(
                    "vision", rs.getString("vision_json") == null ? "" : rs.getString("vision_json"),
                    "answers", rs.getString("answers_json") == null ? "{}" : rs.getString("answers_json"),
                    "status", rs.getString("request_status")), gardenId, requestId);
        if (rows.isEmpty()) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Request not found");
        var row = rows.getFirst();
        String status = row.get("status");
        if ("FAILED".equals(status) || "REJECTED".equals(status)
                || "RECONCILIATION_REQUIRED".equals(status)) {
            return new ContextQuestionResponse("UNAVAILABLE", null, null);
        }
        if (row.get("vision").isBlank()) {
            return new ContextQuestionResponse("WAITING", null, null);
        }
        try {
            JsonNode vision = mapper.readTree(row.get("vision"));
            JsonNode answers = mapper.readTree(row.get("answers"));
            return selector.select(vision, answers)
                    .map(q -> new ContextQuestionResponse("READY", q.key(), q.reason()))
                    .orElseGet(() -> new ContextQuestionResponse("SKIPPED", null, null));
        } catch (com.fasterxml.jackson.core.JsonProcessingException e) {
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Invalid stored analysis");
        }
    }
}
