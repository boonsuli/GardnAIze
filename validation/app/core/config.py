import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    model_path: str = os.getenv("VALID_MODEL_PATH", "/models/garden_resnet18.pt")
    metadata_path: str = os.getenv("VALID_METADATA_PATH", "/models/metadata.json")
    max_image_bytes: int = int(os.getenv("VALID_MAX_IMAGE_BYTES", str(5 * 1024 * 1024)))
    decision_threshold: float = float(os.getenv("VALID_THRESHOLD", "0.70"))

settings = Settings()
