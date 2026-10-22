package com.gardnaize.backend.api;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.gardnaize.backend.domain.Exposure;
import com.gardnaize.backend.domain.SoilType;
import com.gardnaize.backend.service.GardenProjectService;
import java.time.Instant;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(GardenProjectController.class)
class GardenProjectControllerTest {
    @Autowired
    private MockMvc mvc;

    @MockitoBean
    private GardenProjectService service;

    @Test
    void validatesRequest() throws Exception {
        mvc.perform(post("/api/v1/gardens")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void createsGarden() throws Exception {
        UUID id = UUID.randomUUID();
        when(service.create(any())).thenReturn(new GardenProjectResponse(
                id, "Terrace", "Paris", Exposure.FULL_SUN, SoilType.LOAMY, Instant.now()
        ));

        mvc.perform(post("/api/v1/gardens")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                    "name": "Terrace",
                                    "location": "Paris",
                                    "exposure": "FULL_SUN",
                                    "soilType": "LOAMY"
                                }
                                """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.name").value("Terrace"));
    }
}
