"""Plate-first correlation of camera-local ByteTrack observations."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping

from vehicles.normalization import normalize_plate

from .services import TrajectoryService


class MultiCameraCorrelationService:
    """Create chronological, cross-camera journeys without vehicle re-identification.

    Input observations are deliberately plain mappings so this service can be
    proven with local tracker output before any database/API contract changes.
    A normalized plate is the only identity key in this MVP stage.
    """

    @staticmethod
    def _camera_key(observation: Mapping[str, Any]) -> tuple[str, str]:
        camera_id = observation.get('camera_id')
        camera = observation.get('camera') or observation.get('camera_name')
        if camera is None and camera_id is None:
            raise ValueError('Correlation observation requires camera or camera_id.')
        return (str(camera_id or ''), str(camera or f'Camera {camera_id:02d}'))

    @classmethod
    def correlate(cls, observations: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
        """Group plate-readable local tracks into chronological vehicle journeys."""
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for observation in observations:
            plate = normalize_plate(str(observation.get('plate') or ''))
            if not plate:
                continue
            timestamp = observation.get('timestamp')
            TrajectoryService._timestamp_sort_key(timestamp)
            camera_id, camera = cls._camera_key(observation)
            normalized = dict(observation)
            normalized.update({'plate': plate, 'camera_id': camera_id or None, 'camera': camera})
            grouped[plate].append(normalized)

        journeys: dict[str, dict[str, Any]] = {}
        for plate, plate_observations in grouped.items():
            ordered = sorted(plate_observations, key=lambda item: TrajectoryService._timestamp_sort_key(item['timestamp']))
            visits: list[dict[str, Any]] = []
            for observation in ordered:
                camera_key = (observation['camera_id'], observation['camera'])
                if visits and visits[-1]['camera_key'] == camera_key:
                    visit = visits[-1]
                    visit['last_seen'] = observation['timestamp']
                    visit['observation_count'] += 1
                    if observation.get('track_id') is not None:
                        visit['track_ids'].add(observation['track_id'])
                    continue
                visits.append({
                    'camera_key': camera_key,
                    'camera_id': observation['camera_id'],
                    'camera': observation['camera'],
                    'first_seen': observation['timestamp'],
                    'last_seen': observation['timestamp'],
                    'observation_count': 1,
                    'track_ids': {observation['track_id']} if observation.get('track_id') is not None else set(),
                })
            rendered_visits = [
                {key: value for key, value in visit.items() if key != 'camera_key'} | {'track_ids': sorted(visit['track_ids'])}
                for visit in visits
            ]
            journeys[plate] = {
                'plate': plate,
                'first_seen': ordered[0]['timestamp'],
                'last_seen': ordered[-1]['timestamp'],
                'total_observations': len(ordered),
                'camera_sequence': [visit['camera'] for visit in rendered_visits],
                'visits': rendered_visits,
                'observations': ordered,
            }
        return journeys
