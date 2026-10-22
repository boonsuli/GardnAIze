package com.gardnaize.backend.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.when;

import com.gardnaize.backend.api.GardenProjectResponse;
import com.gardnaize.backend.api.RecommendationResponse;
import com.gardnaize.backend.domain.Exposure;
import com.gardnaize.backend.domain.SoilType;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.web.client.RestClient;

class RecommendationServiceTest {
    @Test
    void returnsAiSuggestions() {
        UUID id = UUID.randomUUID();
        GardenProjectService gardens = Mockito.mock(GardenProjectService.class);
        RestClient rest = Mockito.mock(RestClient.class);
        RestClient.RequestBodyUriSpec uri = Mockito.mock(RestClient.RequestBodyUriSpec.class);
        RestClient.ResponseSpec response = Mockito.mock(RestClient.ResponseSpec.class);
        var suggestions = new RecommendationResponse("demo-rules", List.of(
                new RecommendationResponse.PlantSuggestion("Lavender", "Full sun")
        ));

        when(gardens.get(id)).thenReturn(new GardenProjectResponse(
                id, "Garden", "Paris", Exposure.FULL_SUN, SoilType.LOAMY, Instant.now()
        ));
        when(rest.post()).thenReturn(uri);
        when(uri.uri("/recommendations")).thenReturn(uri);
        when(uri.body(Mockito.any())).thenReturn(uri);
        when(uri.retrieve()).thenReturn(response);
        when(response.body(RecommendationResponse.class)).thenReturn(suggestions);

        assertThat(new RecommendationService(gardens, rest).recommend(id).plants()).hasSize(1);
    }
}
