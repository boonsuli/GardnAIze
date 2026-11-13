package com.gardnaize.backend.api;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import org.junit.jupiter.api.Test;

class QuestionnaireCatalogControllerTest {
    @Test
    void questionnaireV2IncludesMatureSpreadAndRootSpace() {
        var catalog = new QuestionnaireCatalogController().get();
        assertEquals(2, catalog.schemaVersion());
        var spread = catalog.questions().stream().filter(q -> q.key().equals("matureSpread")).findFirst().orElseThrow();
        var roots = catalog.questions().stream().filter(q -> q.key().equals("rootSpace")).findFirst().orElseThrow();
        assertEquals(List.of("UNDER_1M","FROM_1_TO_2M","FROM_2_TO_4M","OVER_4M","NO_PREFERENCE"),
                spread.options().stream().map(QuestionnaireCatalogController.Option::value).toList());
        assertEquals(List.of("VERY_LIMITED","LIMITED","MODERATE","UNRESTRICTED","UNKNOWN"),
                roots.options().stream().map(QuestionnaireCatalogController.Option::value).toList());
    }
}
