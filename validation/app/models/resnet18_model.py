"""Load a versioned ResNet-18 checkpoint; never infer with random weights."""
import json
from pathlib import Path
from threading import Lock

class ModelUnavailable(RuntimeError):
    pass

class ResNet18Classifier:
    def __init__(self, model_path: str, metadata_path: str):
        self.model_path = Path(model_path)
        self.metadata_path = Path(metadata_path)
        self._model = None
        self._metadata = None
        self._transform = None
        self._lock = Lock()

    @property
    def ready(self) -> bool:
        return self._model is not None

    @property
    def metadata(self) -> dict:
        return self._metadata or {"name": "resnet18", "version": "unavailable"}

    def load(self) -> None:
        if not self.model_path.is_file() or not self.metadata_path.is_file():
            return
        import torch
        from torchvision import models, transforms
        metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        classes = metadata["classes"]
        if len(classes) < 2 or len(set(classes)) != len(classes):
            raise ValueError("Model metadata must define unique classes")
        model = models.resnet18(weights=None)
        model.fc = torch.nn.Linear(model.fc.in_features, len(classes))
        # Only load checkpoints produced by our trusted training pipeline.
        state = torch.load(self.model_path, map_location="cpu", weights_only=True)
        model.load_state_dict(state)
        model.eval()
        self._transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=metadata.get("mean", [0.485, 0.456, 0.406]),
                                 std=metadata.get("std", [0.229, 0.224, 0.225])),
        ])
        self._metadata = metadata
        self._model = model

    def predict(self, image):
        if not self.ready:
            raise ModelUnavailable("Trained model is not installed")
        import torch
        with self._lock, torch.inference_mode():
            scores = torch.softmax(self._model(self._transform(image).unsqueeze(0)), dim=1)[0]
        index = int(scores.argmax().item())
        return self._metadata["classes"][index], float(scores[index].item())
