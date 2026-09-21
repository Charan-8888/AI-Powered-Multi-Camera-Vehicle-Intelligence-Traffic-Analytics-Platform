from pathlib import Path
from typing import Any

from ultralytics import YOLO


class PlateDetector:
    """Detect number plates within a vehicle crop using a dedicated YOLO model."""

    def __init__(
        self,
        model_path: str | Path | None = None,
        confidence: float = 0.40,
    ) -> None:
        default_model = Path(__file__).resolve().parent.parent / 'models' / 'plate_detector.pt'
        self.model_path = Path(model_path) if model_path else default_model
        self.model = YOLO(str(self.model_path))
        self.confidence = confidence

    def detect(self, vehicle_crop: Any) -> list[dict[str, Any]]:
        """Return dedicated model plate detections for one vehicle crop."""
        if vehicle_crop is None or getattr(vehicle_crop, 'size', 0) == 0:
            return []

        plates = []
        for result in self.model(vehicle_crop, conf=self.confidence, verbose=False):
            if result.boxes is None:
                continue
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                plates.append({
                    'confidence': float(box.conf[0]),
                    'bbox': [x1, y1, x2, y2],
                })
        return plates
