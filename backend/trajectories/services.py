"""Services for reconstructing plate-based vehicle trajectories."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Iterable, Mapping


class TrajectoryService:
    """Build chronological, plate-based trajectories from detection records."""

    @staticmethod
    def _timestamp_sort_key(timestamp: Any) -> datetime:
        if isinstance(timestamp, datetime):
            return timestamp
        if not isinstance(timestamp, str):
            raise ValueError('Detection timestamp must be an ISO 8601 string or datetime.')
        try:
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError as error:
            raise ValueError(f'Invalid detection timestamp: {timestamp!r}') from error

    @classmethod
    def build_trajectory(cls, detections: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
        """Group detections by plate and return their chronological camera routes.

        Each detection must provide ``plate``, ``camera``, and ``timestamp``.
        Blank plates are deliberately ignored because they cannot be correlated
        across cameras. Consecutive visits to the same camera are coalesced in
        ``camera_sequence`` while ``detections`` preserves every source record.
        """
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for detection in detections:
            plate = str(detection.get('plate') or '').strip().upper()
            if not plate:
                continue
            camera = detection.get('camera')
            timestamp = detection.get('timestamp')
            if not camera:
                raise ValueError(f'Missing camera for plate {plate}.')
            cls._timestamp_sort_key(timestamp)
            normalized_detection = dict(detection)
            normalized_detection['plate'] = plate
            grouped[plate].append(normalized_detection)

        trajectories: dict[str, dict[str, Any]] = {}
        for plate, vehicle_detections in grouped.items():
            ordered = sorted(vehicle_detections, key=lambda item: cls._timestamp_sort_key(item['timestamp']))
            camera_sequence: list[str] = []
            for detection in ordered:
                camera = str(detection['camera'])
                if not camera_sequence or camera_sequence[-1] != camera:
                    camera_sequence.append(camera)

            trajectories[plate] = {
                'plate': plate,
                'first_seen': ordered[0]['timestamp'],
                'last_seen': ordered[-1]['timestamp'],
                'total_detections': len(ordered),
                'camera_sequence': camera_sequence,
                'detections': ordered,
            }
        return trajectories
