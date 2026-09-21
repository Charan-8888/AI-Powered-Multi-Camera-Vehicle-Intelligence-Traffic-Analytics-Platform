from typing import Any

from .detector import VehicleDetector
from .ocr import PlateOCR
from .plate_detector import PlateDetector


class VideoProcessor:
    """Coordinates the vehicle → plate → OCR stages for a single frame."""

    def __init__(
        self,
        vehicle_detector: VehicleDetector,
        plate_detector: PlateDetector,
        ocr: PlateOCR,
    ) -> None:
        self.vehicle_detector = vehicle_detector
        self.plate_detector = plate_detector
        self.ocr = ocr

    def process_frame(self, frame: Any) -> list[dict[str, Any]]:
        """Produce an OCR result for each candidate plate in the input frame."""
        return self.process_vehicle_detections(frame, self.vehicle_detector.detect(frame))

    def process_tracked_frame(self, frame: Any, vehicles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Run plate/OCR stages for ByteTrack-annotated vehicle detections."""
        return self.process_vehicle_detections(frame, vehicles)

    def process_vehicle_detections(self, frame: Any, vehicles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Produce OCR results for supplied vehicle detections without redetecting them."""
        results = []
        for candidate in self.detect_vehicle_plates(frame, vehicles=vehicles):
            results.append({
                'vehicle': candidate['vehicle'],
                'plate': candidate['plate'],
                'vehicle_crop': candidate['vehicle_crop'],
                'plate_crop': candidate['plate_crop'],
                'ocr': self.ocr.recognize(candidate['plate_crop']),
            })
        return results

    def detect_vehicle_plates(self, frame: Any, vehicles: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        """Crop each detected vehicle and return its candidate plate regions."""
        if frame is None or getattr(frame, 'size', 0) == 0:
            return []

        frame_height, frame_width = frame.shape[:2]
        results = []
        for vehicle in vehicles if vehicles is not None else self.vehicle_detector.detect(frame):
            bbox = vehicle.get('bbox') if isinstance(vehicle, dict) else None
            if not bbox or len(bbox) != 4:
                continue
            x1, y1, x2, y2 = (int(value) for value in bbox)
            x1, x2 = max(0, x1), min(frame_width, x2)
            y1, y2 = max(0, y1), min(frame_height, y2)
            if x2 <= x1 or y2 <= y1:
                continue

            vehicle_crop = frame[y1:y2, x1:x2]
            for plate in self.plate_detector.detect(vehicle_crop):
                px1, py1, px2, py2 = plate['bbox']
                plate_crop = vehicle_crop[py1:py2, px1:px2]
                if plate_crop.size == 0:
                    continue
                results.append({
                    'vehicle': vehicle,
                    'plate': plate,
                    'vehicle_crop': vehicle_crop,
                    'plate_crop': plate_crop,
                })
        return results
