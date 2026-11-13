package com.gardnaize.backend.api;

import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Backend-owned questionnaire contract. Translation keys are resolved by the UI;
 * never send localized question/answer text across the API.
 */
@RestController
@RequestMapping("/api/v1/questionnaire")
public class QuestionnaireCatalogController {
    public record Option(String value, String labelKey) {}
    public record Question(String key, String labelKey, boolean required,
                           String inputType, List<Option> options) {}
    public record Catalog(int schemaVersion, String externalProcessingNoticeKey,
                          List<Question> questions) {}

    private static Question choice(String key, boolean required, String... values) {
        return new Question(key, "questionnaire." + key + ".label", required, "SINGLE_CHOICE",
            java.util.Arrays.stream(values)
                .map(v -> new Option(v, "questionnaire." + key + ".options." + v))
                .toList());
    }

    private static final Catalog CATALOG = new Catalog(2, "privacy.externalProcessingNotice",
        List.of(
            choice("exposure", true, "FULL_SUN", "PARTIAL_SHADE", "SHADE", "UNKNOWN"),
            choice("soilType", false, "SANDY", "LOAMY", "CLAY", "UNKNOWN"),
            choice("waterAvailability", true, "LOW", "MODERATE", "HIGH"),
            choice("maintenancePreference", true, "LOW", "MODERATE", "HIGH"),
            choice("evergreenPreferred", false, "YES", "NO", "NO_PREFERENCE"),
            choice("privacyScreeningRequired", false, "YES", "NO", "NO_PREFERENCE"),
            choice("desiredHeight", false, "LOW", "MEDIUM", "TALL", "NO_PREFERENCE"),
            choice("matureSpread", false, "UNDER_1M", "FROM_1_TO_2M", "FROM_2_TO_4M", "OVER_4M", "NO_PREFERENCE"),
            choice("rootSpace", false, "VERY_LIMITED", "LIMITED", "MODERATE", "UNRESTRICTED", "UNKNOWN"),
            choice("preferredColors", false, "WHITE", "PINK", "PURPLE", "YELLOW", "NO_PREFERENCE"),
            choice("budget", false, "LOW", "MEDIUM", "HIGH", "NO_PREFERENCE"),
            choice("gardenStyle", false, "CONTEMPORARY", "NATURAL", "MEDITERRANEAN", "NO_PREFERENCE")
        ));

    @GetMapping
    public Catalog get() {
        return CATALOG;
    }
}
