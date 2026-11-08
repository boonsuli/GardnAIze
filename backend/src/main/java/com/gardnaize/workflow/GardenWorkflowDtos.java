package com.gardnaize.workflow;

import java.util.List;
import java.util.Map;
import java.util.UUID;

public final class GardenWorkflowDtos {
    private GardenWorkflowDtos() {}

    public record StoredPhoto(UUID photoId, String status, String message) {}
    public record QuestionOption(String value, String label) {}
    public record Question(String id, String label, String type, boolean required,
                           List<QuestionOption> options) {}
    public record Questionnaire(UUID photoId, List<Question> questions) {}
    public record AnswersRequest(Map<String, Object> answers) {}
    public record AnswersResult(UUID photoId, int savedAnswers, String status) {}
    public record ValidatorResult(String status, String message) {}
}
