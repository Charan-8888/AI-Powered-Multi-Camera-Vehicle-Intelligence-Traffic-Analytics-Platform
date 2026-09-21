from unittest import TestCase

import numpy as np

from .detector import VehicleDetector
from .ocr import PlateOCR
from .ingestion import build_detection_payload
from .plate_detector import PlateDetector
from .processor import VideoProcessor
from .video_runner import VideoRunner
from .tracker import VehicleTracker


class StubVehicleDetector(VehicleDetector):
    def __init__(self):
        pass

    def detect(self, frame):
        return [
            {'vehicle_type': 'car', 'bbox': [0, 0, 50, 50]},
            {'vehicle_type': 'bus', 'bbox': [50, 0, 100, 50]},
        ]


class StubPlateDetector(PlateDetector):
    def __init__(self):
        pass

    def detect(self, vehicle_crop):
        return [{'bbox': [5, 5, 25, 15], 'area': 200, 'aspect_ratio': 2.0}]


class StubOCR(PlateOCR):
    def __init__(self):
        pass

    def recognize(self, plate_crop):
        return {
            'text': 'KA01AB1234',
            'normalized_text': 'KA01AB1234',
            'confidence': 0.99,
        }


class VideoProcessorTests(TestCase):
    def test_plate_text_normalization(self):
        self.assertEqual(PlateOCR.normalize_plate(' TS 09-AB 1234 '), 'TS09AB1234')

    def test_processes_every_plate_from_every_vehicle(self):
        processor = VideoProcessor(StubVehicleDetector(), StubPlateDetector(), StubOCR())

        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        candidates = processor.detect_vehicle_plates(frame)
        results = processor.process_frame(frame)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['vehicle']['vehicle_type'], 'car')
        self.assertEqual(results[1]['vehicle']['vehicle_type'], 'bus')
        self.assertEqual(candidates[0]['plate_crop'].shape, (10, 20, 3))
        self.assertEqual(results[0]['ocr']['normalized_text'], 'KA01AB1234')
        self.assertEqual(results[0]['vehicle_crop'].shape, (50, 50, 3))
        self.assertEqual(results[0]['plate_crop'].shape, (10, 20, 3))

    def test_complete_pipeline_returns_normalized_plate(self):
        processor = VideoProcessor(StubVehicleDetector(), StubPlateDetector(), StubOCR())

        results = processor.process_frame(np.zeros((100, 100, 3), dtype=np.uint8))

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['vehicle']['vehicle_type'], 'car')
        self.assertEqual(results[0]['ocr']['normalized_text'], 'KA01AB1234')

    def test_builds_detection_payload_from_fake_cv_result(self):
        result = {
            'vehicle': {'vehicle_type': 'car', 'confidence': 0.91, 'bbox': [100, 100, 400, 300]},
            'plate': {'confidence': 0.94, 'bbox': [150, 220, 300, 260]},
            'ocr': {'text': 'TS-09 AB 1234', 'normalized_text': 'TS09AB1234', 'confidence': 0.97},
        }

        payload = build_detection_payload(result, camera_id=1, timestamp='2026-09-21T10:15:23Z')

        self.assertEqual(payload, {
            'plate': 'TS09AB1234', 'camera_id': 1, 'timestamp': '2026-09-21T10:15:23Z',
            'plate_confidence': 0.97, 'vehicle_confidence': 0.91, 'vehicle_type': 'car',
        })

    def test_runner_suppresses_nearby_duplicate_plates(self):
        runner = VideoRunner('unused.mp4', 1, processor=None, duplicate_interval_seconds=10)
        moment = __import__('datetime').datetime(2026, 9, 21, tzinfo=__import__('datetime').timezone.utc)
        self.assertTrue(runner._should_submit('TS09AB1234', moment))
        self.assertFalse(runner._should_submit('TS09AB1234', moment + __import__('datetime').timedelta(seconds=9)))
        self.assertTrue(runner._should_submit('TS09AB1234', moment + __import__('datetime').timedelta(seconds=10)))

    def test_tracker_exposes_persistent_track_ids(self):
        class Box:
            cls, conf, id = [2], [0.91], 17
            class XYXY:
                def tolist(self): return [1, 2, 30, 40]
            xyxy = [XYXY()]
        class Model:
            def track(self, *args, **kwargs):
                return [type('Result', (), {'boxes': [Box()]})()]
        detector = StubVehicleDetector()
        detector.model = Model()
        detector.confidence = 0.35
        detections = VehicleTracker(detector).track(np.zeros((10, 10, 3), dtype=np.uint8))
        self.assertEqual(detections, [{
            'track_id': 17, 'class_id': 2, 'vehicle_type': 'car',
            'confidence': 0.91, 'bbox': [1, 2, 30, 40],
        }])
