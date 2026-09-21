"""Small ByteTrack adapter for the existing Ultralytics vehicle detector."""

from __future__ import annotations

from typing import Any

from .detector import VehicleDetector


class VehicleTracker:
    """Assign persistent, per-video IDs to supported vehicle detections.

    This deliberately owns no database state.  Ultralytics keeps the ByteTrack
    state on the model while ``persist=True`` is used for sequential frames.
    """

    def __init__(self, vehicle_detector: VehicleDetector, tracker: str = 'bytetrack.yaml') -> None:
        self.vehicle_detector = vehicle_detector
        self.tracker = tracker

    @staticmethod
    def _value(value: Any) -> Any:
        """Extract a Python scalar from Torch/Numpy scalars and test doubles."""
        if hasattr(value, 'item'):
            return value.item()
        if isinstance(value, (list, tuple)):
            return value[0] if value else None
        return value

    def track(self, frame: Any, frame_number: int | None = None, timestamp: str | None = None) -> list[dict[str, Any]]:
        """Return supported vehicle detections annotated with a ByteTrack ID."""
        if frame is None or getattr(frame, 'size', 0) == 0:
            return []

        detections = []
        results = self.vehicle_detector.model.track(
            frame,
            persist=True,
            tracker=self.tracker,
            conf=self.vehicle_detector.confidence,
            verbose=False,
        )
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                class_id = int(self._value(box.cls[0]))
                if class_id not in self.vehicle_detector.VEHICLE_CLASSES:
                    continue
                track_id = self._value(box.id)
                if track_id is None:
                    continue
                detection = {
                    'track_id': int(track_id),
                    'class_id': class_id,
                    'vehicle_type': self.vehicle_detector.VEHICLE_CLASSES[class_id],
                    'confidence': float(self._value(box.conf[0])),
                    'bbox': [int(value) for value in box.xyxy[0].tolist()],
                }
                if frame_number is not None:
                    detection['frame_number'] = frame_number
                if timestamp is not None:
                    detection['timestamp'] = timestamp
                detections.append(detection)
        return detections
