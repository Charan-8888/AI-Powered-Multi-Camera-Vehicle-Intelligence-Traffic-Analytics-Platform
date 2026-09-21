"""Controlled, single-camera prerecorded-video integration harness."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from time import monotonic
from typing import Any, Callable

import cv2
import requests

from .ingestion import build_detection_payload
from .processor import VideoProcessor


class VideoRunner:
    """Sample frames, persist usable OCR results, and emit a demo-friendly report."""

    def __init__(
        self, video_path: str, camera_id: int, processor: VideoProcessor,
        api_base_url: str = 'http://127.0.0.1:8000/api', frame_stride: int = 10,
        duplicate_interval_seconds: float = 10, post: Callable[..., Any] = requests.post,
    ) -> None:
        if frame_stride < 1:
            raise ValueError('frame_stride must be at least 1.')
        self.video_path = video_path
        self.camera_id = camera_id
        self.processor = processor
        self.api_base_url = api_base_url.rstrip('/')
        self.frame_stride = frame_stride
        self.duplicate_interval = timedelta(seconds=duplicate_interval_seconds)
        self.post = post
        self.last_submitted: dict[str, datetime] = {}

    def _should_submit(self, plate: str, timestamp: datetime) -> bool:
        previous = self.last_submitted.get(plate)
        if previous and timestamp - previous < self.duplicate_interval:
            return False
        self.last_submitted[plate] = timestamp
        return True

    def run(self) -> dict[str, Any]:
        capture = cv2.VideoCapture(self.video_path)
        if not capture.isOpened():
            raise ValueError(f'Unable to open video: {self.video_path}')
        started = monotonic()
        report = Counter()
        report['video'] = self.video_path
        report['camera_id'] = self.camera_id
        fps = capture.get(cv2.CAP_PROP_FPS) or 1
        frame_index = 0
        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                report['frames_read'] += 1
                if frame_index % self.frame_stride:
                    frame_index += 1
                    continue
                report['frames_processed'] += 1
                timestamp = datetime.now(timezone.utc) + timedelta(seconds=frame_index / fps)
                for result in self.processor.process_frame(frame):
                    report['vehicle_detections'] += 1
                    if result.get('plate'):
                        report['plate_candidates'] += 1
                    if result.get('ocr'):
                        report['ocr_results'] += 1
                    try:
                        payload = build_detection_payload(result, camera_id=self.camera_id, timestamp=timestamp)
                    except ValueError:
                        report['discarded_ocr_results'] += 1
                        continue
                    report['valid_normalized_plates'] += 1
                    if not self._should_submit(payload['plate'], timestamp):
                        report['duplicate_submissions_skipped'] += 1
                        continue
                    response = self.post(f'{self.api_base_url}/detections/', json=payload, timeout=10)
                    if response.ok:
                        report['api_detections_created'] += 1
                    else:
                        report['api_submission_failures'] += 1
                        report['last_api_error'] = f'{response.status_code}: {response.text}'
                frame_index += 1
        finally:
            capture.release()
        report['elapsed_seconds'] = round(monotonic() - started, 2)
        return dict(report)

    @staticmethod
    def format_report(report: dict[str, Any]) -> str:
        return '\n'.join((
            '=== VIDEO INTEGRATION REPORT ===',
            f"Video: {report['video']}", f"Camera ID: {report['camera_id']}",
            f"Frames read: {report.get('frames_read', 0)}", f"Frames processed: {report.get('frames_processed', 0)}",
            f"Vehicles detected: {report.get('vehicle_detections', 0)}", f"Plate candidates: {report.get('plate_candidates', 0)}",
            f"OCR results: {report.get('ocr_results', 0)}", f"Valid normalized plates: {report.get('valid_normalized_plates', 0)}",
            f"Duplicate submissions skipped: {report.get('duplicate_submissions_skipped', 0)}",
            f"API detections created: {report.get('api_detections_created', 0)}", f"Elapsed time: {report.get('elapsed_seconds', 0)}s",
            f"API submission failures: {report.get('api_submission_failures', 0)}",
            f"Last API error: {report.get('last_api_error', 'none')}",
        ))
