from uuid import uuid4
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from app.core.config import settings
from app.models.resnet18_model import ModelUnavailable
from app.schemas.validation_response import ValidationResponse
from app.services.image_preprocessing import decode_image
from app.services.validation_service import classifier, validate

router = APIRouter(prefix="/api/v1", tags=["validation"])

@router.get("/health")
def health():
    return {"status": "ok", "model_ready": classifier.ready}

@router.get("/model/info")
def model_info():
    return {"ready": classifier.ready, **classifier.metadata}

@router.post("/validation/photo", response_model=ValidationResponse,
             responses={413: {"description": "Image too large"}, 415: {"description": "Unsupported image"},
                        422: {"description": "Invalid image"}, 503: {"description": "Model unavailable"}})
def validate_photo(photo: UploadFile = File(...), description: str = Form(default=""),
                   request_id: str | None = Form(default=None)):
    if len(description) > 1000:
        raise HTTPException(422, "Description exceeds 1000 characters")
    if photo.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(415, "Unsupported image type")
    content = photo.file.read(settings.max_image_bytes + 1)
    if len(content) > settings.max_image_bytes:
        raise HTTPException(413, "Image too large")
    try:
        image = decode_image(content, photo.content_type)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    try:
        return validate(image, request_id or str(uuid4()))
    except ModelUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
