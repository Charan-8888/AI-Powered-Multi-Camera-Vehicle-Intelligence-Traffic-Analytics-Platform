"""Evidence-bound trajectory facts and narrative explanations."""

from __future__ import annotations

from statistics import mean
from typing import Any, Mapping

from .services import TrajectoryService


class TrajectoryIntelligenceService:
    """Calculate facts from a correlated journey without changing it."""

    @classmethod
    def summarize(
        cls, journey: Mapping[str, Any], *, short_transition_seconds: int = 60,
        long_transition_seconds: int = 900,
    ) -> dict[str, Any]:
        visits = list(journey.get('visits') or [])
        if not visits:
            raise ValueError('A journey needs at least one camera visit.')
        route = [visit['camera'] for visit in visits]
        first, last = visits[0], visits[-1]
        transitions = []
        for previous, current in zip(visits, visits[1:]):
            elapsed = int((
                TrajectoryService._timestamp_sort_key(current['first_seen'])
                - TrajectoryService._timestamp_sort_key(previous['last_seen'])
            ).total_seconds())
            flag = 'short' if elapsed < short_transition_seconds else 'long' if elapsed > long_transition_seconds else None
            transitions.append({
                'from': previous['camera'], 'to': current['camera'],
                'elapsed_seconds': elapsed, 'interval_flag': flag,
            })
        confidences = [
            float(observation['confidence']) for observation in journey.get('observations', [])
            if observation.get('confidence') is not None
        ]
        started = TrajectoryService._timestamp_sort_key(first['first_seen'])
        ended = TrajectoryService._timestamp_sort_key(last['last_seen'])
        return {
            'plate': journey['plate'],
            'first_seen': {'camera': first['camera'], 'timestamp': first['first_seen']},
            'last_seen': {'camera': last['camera'], 'timestamp': last['last_seen']},
            'camera_visits': len(visits),
            'route': route,
            'total_observation_duration_seconds': int((ended - started).total_seconds()),
            'transitions': transitions,
            'average_confidence': round(mean(confidences), 4) if confidences else None,
            'lowest_confidence': min(confidences) if confidences else None,
        }


class EvidenceBoundTrajectoryExplainer:
    """Render only supplied trajectory facts; never infer roads, motives, or identity."""

    @staticmethod
    def explain(facts: Mapping[str, Any]) -> str:
        first = facts['first_seen']
        last = facts['last_seen']
        route = facts['route']
        narrative = (
            f"Vehicle {facts['plate']} was first observed at {first['camera']} at {first['timestamp']} "
            f"and last observed at {last['camera']} at {last['timestamp']}. "
        )
        if len(route) > 1:
            middle = ', '.join(route[1:-1])
            narrative += f"The recorded camera sequence is {' -> '.join(route)}."
            if middle:
                narrative += f" Intermediate recorded camera(s): {middle}."
        else:
            narrative += f"It has one recorded camera visit at {route[0]}."
        return narrative
