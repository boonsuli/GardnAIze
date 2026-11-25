package com.gardnaize.backend.api;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
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

/** Poll persisted recommendations; never invokes PLANT on GET. */
@RestController
@RequestMapping("/api/v1/gardens/{gardenId}/photo-requests/{requestId}/recommendations")
public class PlantRecommendationController {
    private final JdbcTemplate jdbc;
    private final ObjectMapper mapper;

    public PlantRecommendationController(JdbcTemplate jdbc, ObjectMapper mapper) {
        this.jdbc=jdbc; this.mapper=mapper;
    }

    @GetMapping
    @Operation(summary="Read persisted GDAI-PLANT recommendations after completion")
    public Map<String,Object> get(@PathVariable UUID gardenId, @PathVariable UUID requestId) {
        var rows=jdbc.query("""
            SELECT r.status, x.recommendations::text AS recommendations,
                   x.method, x.model_version
            FROM public.garden_photo_requests r
            LEFT JOIN public.garden_photo_recommendations x ON x.request_id=r.request_id
            WHERE r.garden_id=? AND r.request_id=?
            """, (rs,i)->new Object[]{
                rs.getString("status"),rs.getString("recommendations"),
                rs.getString("method"),rs.getString("model_version")
            },gardenId,requestId);
        if(rows.isEmpty()) throw new ResponseStatusException(HttpStatus.NOT_FOUND,"Request not found");
        var row=rows.getFirst();
        String status=(String)row[0];
        if(!"COMPLETED".equals(status) || row[1]==null)
            return Map.of("requestId",requestId.toString(),"status",status,"recommendations",java.util.List.of());
        try {
            JsonNode results=mapper.readTree((String)row[1]);
            Map<String,Object> response=new java.util.LinkedHashMap<>();
            response.put("requestId",requestId.toString());
            response.put("status",status);
            response.put("recommendationCount",results.size());
            response.put("recommendations",results);
            response.put("method",row[2]);
            response.put("modelVersion",row[3]);
            return response;
        } catch (com.fasterxml.jackson.core.JsonProcessingException e) {
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR,"Stored recommendations invalid");
        }
    }
}
