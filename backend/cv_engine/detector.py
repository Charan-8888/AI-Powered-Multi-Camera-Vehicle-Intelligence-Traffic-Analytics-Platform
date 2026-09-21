import os
from pathlib import Path
from typing import Any

# Keep Ultralytics configuration inside the project, not in a protected user-profile folder.
os.environ.setdefault('YOLO_CONFIG_DIR', str(Path(__file__).resolve().parent.parent / 'runtime'))

from ultralytics import YOLO


class VehicleDetector:
    """Detect cars, motorcycles, buses, and trucks in an OpenCV frame with YOLO."""

    VEHICLE_CLASSES = {
        2: 'car',
        3: 'motorcycle',
        5: 'bus',
        7: 'truck',
    }

    def __init__(self, model_path: str = 'yolo11n.pt', confidence: float = 0.35) -> None:
        self.model = YOLO(model_path)
        self.confidence = confidence

    def detect(self, frame: Any) -> list[dict[str, Any]]:
        """Return normalized vehicle detections from one OpenCV image/frame."""
        detections = []
        for result in self.model(frame, conf=self.confidence, verbose=False):
            if result.boxes is None:
                continue
            for box in result.boxes:
                class_id = int(box.cls[0])
                if class_id not in self.VEHICLE_CLASSES:
                    continue
                detections.append({
                    'class_id': class_id,
                    'vehicle_type': self.VEHICLE_CLASSES[class_id],
                    'confidence': float(box.conf[0]),
                    'bbox': [int(value) for value in box.xyxy[0].tolist()],
                })
        return detections
