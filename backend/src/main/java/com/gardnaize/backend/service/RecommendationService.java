package com.gardnaize.backend.service;

import com.gardnaize.backend.api.GardenProjectResponse;
import com.gardnaize.backend.api.RecommendationResponse;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.server.ResponseStatusException;

@Service
public class RecommendationService {
    private final GardenProjectService gardenService;
    private final RestClient aiRestClient;

    public RecommendationService(GardenProjectService gardenService, RestClient aiRestClient) {
        this.gardenService = gardenService;
        this.aiRestClient = aiRestClient;
    }

    public RecommendationResponse recommend(UUID gardenId) {
        GardenProjectResponse garden = gardenService.get(gardenId);

        try {
            RecommendationResponse result = aiRestClient.post()
                    .uri("/recommendations")
                    .body(new RecommendationRequest(
                            garden.location(),
                            garden.exposure().name(),
                            garden.soilType().name()
                    ))
                    .retrieve()
                    .body(RecommendationResponse.class);

            if (result == null) {
                throw new ResponseStatusException(
                        HttpStatus.BAD_GATEWAY, "Empty response from AI service"
                );
            }

            return result;
        } catch (RestClientException exception) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_GATEWAY, "AI recommendation service unavailable"
            );
        }
    }

    private record RecommendationRequest(String location, String exposure, String soilType) {
    }
}
