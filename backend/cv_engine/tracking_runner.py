"""Local temporal-tracking harness; it intentionally does not write to the API."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from time import monotonic
from typing import Any

import cv2

from .processor import VideoProcessor
from .tracker import VehicleTracker


class TrackingRunner:
    """Run ByteTrack across a video and associate sampled OCR output with tracks."""

    def __init__(self, video_path: str, tracker: VehicleTracker, processor: VideoProcessor, frame_stride: int = 10) -> None:
        if frame_stride < 1:
            raise ValueError('frame_stride must be at least 1.')
        self.video_path = video_path
        self.tracker = tracker
        self.processor = processor
        self.frame_stride = frame_stride

    def run(self) -> dict[str, Any]:
        capture = cv2.VideoCapture(self.video_path)
        if not capture.isOpened():
            raise ValueError(f'Unable to open video: {self.video_path}')

        started = monotonic()
        fps = capture.get(cv2.CAP_PROP_FPS) or 1
        frame_number = 0
        tracks: dict[int, dict[str, Any]] = {}
        report: dict[str, Any] = {
            'video': self.video_path,
            'frames_read': 0,
            'frames_processed': 0,
            'vehicle_observations': 0,
        }
        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                report['frames_read'] += 1
                timestamp = datetime.now(timezone.utc) + timedelta(seconds=frame_number / fps)
                vehicles = self.tracker.track(frame, frame_number=frame_number, timestamp=timestamp.isoformat())
                for vehicle in vehicles:
                    track = tracks.setdefault(vehicle['track_id'], {
                        'track_id': vehicle['track_id'],
                        'vehicle_type': vehicle['vehicle_type'],
                        'observations': 0,
                        'plates': {},
                        'first_frame': frame_number,
                        'last_frame': frame_number,
                    })
                    track['observations'] += 1
                    track['last_frame'] = frame_number
                    report['vehicle_observations'] += 1

                if frame_number % self.frame_stride == 0:
                    report['frames_processed'] += 1
                    for result in self.processor.process_tracked_frame(frame, vehicles):
                        track = tracks[result['vehicle']['track_id']]
                        ocr = result.get('ocr') or {}
                        plate = ocr.get('normalized_text')
                        if plate:
                            current = track['plates'].get(plate, 0.0)
                            track['plates'][plate] = max(current, float(ocr.get('confidence') or 0))
                frame_number += 1
        finally:
            capture.release()

        summaries = []
        for track in sorted(tracks.values(), key=lambda item: item['track_id']):
            plate = max(track['plates'], key=track['plates'].get, default=None)
            summaries.append({
                'track_id': track['track_id'],
                'vehicle_type': track['vehicle_type'],
                'observations': track['observations'],
                'plate': plate,
                'plate_confidence': track['plates'].get(plate) if plate else None,
                'first_frame': track['first_frame'],
                'last_frame': track['last_frame'],
            })
        report['tracks'] = summaries
        report['unique_vehicle_tracks'] = len(summaries)
        report['tracks_with_plate_ocr'] = sum(track['plate'] is not None for track in summaries)
        report['unique_normalized_plates'] = len({track['plate'] for track in summaries if track['plate']})
        report['elapsed_seconds'] = round(monotonic() - started, 2)
        return report

    @staticmethod
    def format_report(report: dict[str, Any]) -> str:
        lines = [
            '=== TRACKING REPORT ===',
            f"Video: {report['video']}",
            f"Frames read: {report.get('frames_read', 0)}",
            f"Frames processed: {report.get('frames_processed', 0)}",
            f"Unique vehicle tracks: {report.get('unique_vehicle_tracks', 0)}",
            f"Vehicle observations: {report.get('vehicle_observations', 0)}",
            f"Tracks with plate OCR: {report.get('tracks_with_plate_ocr', 0)}",
            f"Unique normalized plates: {report.get('unique_normalized_plates', 0)}",
            f"Elapsed time: {report.get('elapsed_seconds', 0)}s",
        ]
        plate_tracks = [track for track in report.get('tracks', []) if track['plate']]
        most_observed = sorted(report.get('tracks', []), key=lambda track: track['observations'], reverse=True)
        displayed_tracks = {track['track_id']: track for track in plate_tracks + most_observed[:5]}
        for track in displayed_tracks.values():
            lines.extend((
                '', f"Track #{track['track_id']}:",
                f"  vehicle_type: {track['vehicle_type']}",
                f"  observations: {track['observations']}",
                f"  frame range: {track['first_frame']}–{track['last_frame']}",
                f"  plate: {track['plate'] or 'unread'}",
            ))
        return '\n'.join(lines)
