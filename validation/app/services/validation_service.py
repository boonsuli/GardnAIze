from app.core.config import settings
from app.models.resnet18_model import ResNet18Classifier
from app.schemas.validation_response import ModelInfo, ValidationResponse

classifier = ResNet18Classifier(settings.model_path, settings.metadata_path)

def validate(image, request_id: str) -> ValidationResponse:
    predicted_class, confidence = classifier.predict(image)
    threshold = float(classifier.metadata.get("threshold", settings.decision_threshold))
    valid = predicted_class == "garden" and confidence >= threshold
    return ValidationResponse(
        request_id=request_id,
        valid=valid,
        status="VALID" if valid else "INVALID",
        confidence=confidence,
        predicted_class=predicted_class,
        model=ModelInfo(name="resnet18", version=classifier.metadata["version"]),
        reason_code=None if valid else ("LOW_CONFIDENCE" if predicted_class == "garden" else "NOT_A_GARDEN"),
        message="Photo de jardin valide" if valid else "Photo non valide",
    )
