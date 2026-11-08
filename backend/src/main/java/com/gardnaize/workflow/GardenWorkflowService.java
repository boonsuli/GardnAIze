package com.gardnaize.workflow;

import com.gardnaize.workflow.GardenWorkflowDtos.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestClient;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import java.io.IOException;
import java.util.*;
import static org.springframework.http.HttpStatus.*;

@Service
public class GardenWorkflowService {
    private final JdbcTemplate jdbc;
    private final RestClient validator;
    private final String validatorUrl;

    public GardenWorkflowService(JdbcTemplate jdbc, RestClient.Builder restClientBuilder,
            @Value("${gardnaize.validation.base-url:http://localhost:9001}") String validatorUrl) {
        this.jdbc = jdbc;
        this.validator = restClientBuilder.build();
        this.validatorUrl = validatorUrl;
    }

    // The internal GDAI-FRONT server submits bytes only after user confirmation.
    // GDAI-BACK verifies them again with GDAI-VALID before storing in PostgreSQL.
    @Transactional
    public StoredPhoto validateAndPersist(MultipartFile photo, String description) throws IOException {
        if (photo.isEmpty() || photo.getSize() > 1_048_576) {
            throw new ResponseStatusException(PAYLOAD_TOO_LARGE, "Image must be between 1 byte and 1 MiB");
        }
        byte[] bytes = photo.getBytes();
        String mime = detectMime(bytes);
        if (mime == null) throw new ResponseStatusException(UNSUPPORTED_MEDIA_TYPE, "Unsupported image format");
        ValidatorResult result;
        try {
            result = validator.post().uri(validatorUrl + "/validate")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(buildValidatorBody(bytes, mime))
                .retrieve().body(ValidatorResult.class);
        } catch (Exception ex) {
            throw new ResponseStatusException(BAD_GATEWAY, "GDAI-VALID unavailable", ex);
        }
        if (result == null || !"VALID".equalsIgnoreCase(result.status())) {
            return new StoredPhoto(null, "INVALID",
                result == null ? "No validation response" : result.message());
        }
        UUID id = UUID.randomUUID();
        jdbc.update("INSERT INTO gdai_validated_photos(id,original_filename,mime_type,description,image_data,image_size_bytes) VALUES (?,?,?,?,?,?)",
            id, safeName(photo.getOriginalFilename()), mime,
            description == null ? "" : description.strip(), bytes, bytes.length);
        return new StoredPhoto(id, "VALID", "Photo valide");
    }

    private org.springframework.util.MultiValueMap<String, Object> buildValidatorBody(byte[] bytes, String mime) {
        var map = new org.springframework.util.LinkedMultiValueMap<String, Object>();
        var part = new org.springframework.core.io.ByteArrayResource(bytes) {
            @Override public String getFilename() { return "garden-image"; }
        };
        var headers = new org.springframework.http.HttpHeaders();
        headers.setContentType(MediaType.parseMediaType(mime));
        map.add("photo", new org.springframework.http.HttpEntity<>(part, headers));
        return map;
    }

    private String detectMime(byte[] b) {
        if (b.length >= 3 && (b[0] & 255) == 255 && (b[1] & 255) == 216 && (b[2] & 255) == 255)
            return "image/jpeg";
        if (b.length >= 8 && (b[0] & 255) == 137 && b[1] == 80 && b[2] == 78 && b[3] == 71)
            return "image/png";
        if (b.length >= 12 && b[0] == 'R' && b[1] == 'I' && b[2] == 'F' && b[3] == 'F'
                && b[8] == 'W' && b[9] == 'E' && b[10] == 'B' && b[11] == 'P')
            return "image/webp";
        return null;
    }

    private String safeName(String original) {
        if (original == null) return "garden-image";
        String name = original.replace('\\', '/');
        name = name.substring(name.lastIndexOf('/') + 1);
        return name.replaceAll("[^a-zA-Z0-9._-]", "_").substring(0, Math.min(name.length(), 200));
    }

    public Questionnaire questions(UUID photoId, String language, String continent, String climate, String country) {
        requirePhoto(photoId);
        String lang = "en".equalsIgnoreCase(language) ? "en" : "fr";
        String sql = """
            SELECT q.id, q.answer_type, q.required, COALESCE(t.label, fallback.label, q.id) AS label
            FROM gdai_questions q
            LEFT JOIN gdai_question_translations t ON t.question_id=q.id AND t.language_code=?
            LEFT JOIN gdai_question_translations fallback ON fallback.question_id=q.id AND fallback.language_code='en'
            WHERE q.active=TRUE AND (
                NOT EXISTS (SELECT 1 FROM gdai_question_rules r WHERE r.question_id=q.id)
                OR EXISTS (SELECT 1 FROM gdai_question_rules r WHERE r.question_id=q.id
                    AND (r.continent_code IS NULL OR r.continent_code=?)
                    AND (r.climate_code IS NULL OR r.climate_code=?)
                    AND (r.country_code IS NULL OR r.country_code=?))
            )
            ORDER BY q.display_order LIMIT 10
            """;
        var questions = jdbc.query(sql, (rs, row) -> new Question(
            rs.getString("id"), rs.getString("label"), rs.getString("answer_type"),
            rs.getBoolean("required"), options(rs.getString("id"), lang)),
            lang, continent, climate, country);
        return new Questionnaire(photoId, questions);
    }

    private List<QuestionOption> options(String id, String language) {
        return jdbc.query("""
            SELECT o.value, COALESCE(t.label, fallback.label, o.value) AS label
            FROM gdai_question_options o
            LEFT JOIN gdai_question_option_translations t ON t.question_id=o.question_id
                AND t.value=o.value AND t.language_code=?
            LEFT JOIN gdai_question_option_translations fallback ON fallback.question_id=o.question_id
                AND fallback.value=o.value AND fallback.language_code='en'
            WHERE o.question_id=? ORDER BY o.display_order
            """, (rs, row) -> new QuestionOption(rs.getString(1), rs.getString(2)), language, id);
    }

    @Transactional
    public AnswersResult saveAnswers(UUID photoId, Map<String, Object> answers,
                                      String language, String continent, String climate, String country) {
        Questionnaire questionnaire = questions(photoId, language, continent, climate, country);
        Map<String, Question> allowed = new HashMap<>();
        for (Question question : questionnaire.questions()) allowed.put(question.id(), question);
        if (answers == null) throw new ResponseStatusException(BAD_REQUEST, "Missing answers");
        for (Question question : questionnaire.questions()) {
            if (question.required() && (answers.get(question.id()) == null ||
                answers.get(question.id()).toString().isBlank()))
                throw new ResponseStatusException(BAD_REQUEST, "Missing required answer: " + question.id());
        }
        for (var entry : answers.entrySet()) {
            Question question = allowed.get(entry.getKey());
            if (question == null) throw new ResponseStatusException(BAD_REQUEST, "Unknown question: " + entry.getKey());
            Object value = entry.getValue();
            if (value == null) continue;
            String stringValue = value.toString();
            if (stringValue.length() > 500) throw new ResponseStatusException(BAD_REQUEST, "Answer too long");
            if ("select".equals(question.type()) &&
                question.options().stream().noneMatch(o -> o.value().equals(stringValue)))
                throw new ResponseStatusException(BAD_REQUEST, "Invalid choice for " + entry.getKey());
            if ("boolean".equals(question.type()) && !List.of("true", "false").contains(stringValue))
                throw new ResponseStatusException(BAD_REQUEST, "Invalid boolean");
            if ("number".equals(question.type())) {
                try { Double.parseDouble(stringValue); }
                catch (NumberFormatException ex) { throw new ResponseStatusException(BAD_REQUEST, "Invalid number"); }
            }
            jdbc.update("""
                INSERT INTO gdai_garden_answers(photo_id,question_id,answer_value)
                VALUES (?,?,?) ON CONFLICT (photo_id,question_id)
                DO UPDATE SET answer_value=EXCLUDED.answer_value, answered_at=now()
                """, photoId, entry.getKey(), stringValue);
        }
        return new AnswersResult(photoId, answers.size(), "SAVED");
    }

    private void requirePhoto(UUID photoId) {
        Integer count = jdbc.queryForObject(
            "SELECT count(*) FROM gdai_validated_photos WHERE id=?", Integer.class, photoId);
        if (count == null || count == 0) throw new ResponseStatusException(NOT_FOUND, "Photo not found");
    }
}
