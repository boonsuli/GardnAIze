package com.gardnaize.backend.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.HashMap;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;
import static org.junit.jupiter.api.Assertions.*;

class StagedQuestionnaireValidationTest {
    private final ObjectMapper mapper = new ObjectMapper();

    @Test void acceptsCatalogValues() throws Exception {
        StagedPhotoIntakeService.validateOptions(mapper.readTree("""
            {"exposure":"FULL_SUN","waterAvailability":"LOW",
             "maintenancePreference":"HIGH","privacyScreeningRequired":"YES",
             "rootSpace":"LIMITED","matureSpread":"UNDER_1M"}
            """));
    }

    @Test void rejectsInvalidValuesAndTypes() throws Exception {
        for (String json : new String[]{
                "{\"privacyScreeningRequired\":true}",
                "{\"rootSpace\":\"INVALID\"}",
                "{\"exposure\":null}",
                "{\"_contextQuestion\":{}}",
                "{\"waterAvailability\":\"\"}"}) {
            var node = mapper.readTree(json);
            var ex = assertThrows(ResponseStatusException.class,
                    () -> StagedPhotoIntakeService.validateOptions(node));
            assertEquals(400, ex.getStatusCode().value());
        }
    }

    @Test void mapsPreferencesWithoutInventingNoPreference() {
        var profile = new HashMap<String,Object>();
        PlantRecommendationWorker.putPreference(profile, "yes", mapper.getNodeFactory().textNode("YES"));
        PlantRecommendationWorker.putPreference(profile, "no", mapper.getNodeFactory().textNode("NO"));
        PlantRecommendationWorker.putPreference(profile, "unset", mapper.getNodeFactory().textNode("NO_PREFERENCE"));
        assertEquals(true, profile.get("yes"));
        assertEquals(false, profile.get("no"));
        assertFalse(profile.containsKey("unset"));
    }
}
