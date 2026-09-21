from django.test import SimpleTestCase

from .services import TrajectoryService
from .correlation import MultiCameraCorrelationService
from .intelligence import EvidenceBoundTrajectoryExplainer, TrajectoryIntelligenceService


class TrajectoryServiceTests(SimpleTestCase):
    def test_builds_chronological_trajectory(self):
        detections = [
            {'plate': 'TS09AB1234', 'camera': 'Camera 03', 'timestamp': '2026-09-21T10:17:41'},
            {'plate': 'TS09AB1234', 'camera': 'Camera 01', 'timestamp': '2026-09-21T10:15:23'},
            {'plate': 'TS09AB1234', 'camera': 'Camera 02', 'timestamp': '2026-09-21T10:20:08'},
        ]

        trajectory = TrajectoryService.build_trajectory(detections)['TS09AB1234']

        self.assertEqual(trajectory['camera_sequence'], ['Camera 01', 'Camera 03', 'Camera 02'])
        self.assertEqual(trajectory['first_seen'], '2026-09-21T10:15:23')
        self.assertEqual(trajectory['last_seen'], '2026-09-21T10:20:08')
        self.assertEqual(trajectory['total_detections'], 3)

    def test_coalesces_consecutive_camera_visits_and_ignores_blank_plates(self):
        detections = [
            {'plate': 'ka01 ab1234', 'camera': 'Camera 01', 'timestamp': '2026-09-21T10:00:00'},
            {'plate': 'KA01 AB1234', 'camera': 'Camera 01', 'timestamp': '2026-09-21T10:01:00'},
            {'plate': '', 'camera': 'Camera 99', 'timestamp': '2026-09-21T10:02:00'},
        ]

        result = TrajectoryService.build_trajectory(detections)

        self.assertEqual(list(result), ['KA01 AB1234'])
        self.assertEqual(result['KA01 AB1234']['camera_sequence'], ['Camera 01'])
        self.assertEqual(result['KA01 AB1234']['total_detections'], 2)


class MultiCameraCorrelationServiceTests(SimpleTestCase):
    def test_correlates_one_plate_across_cameras_in_chronological_order(self):
        observations = [
            {'plate': 'lr60 wjz', 'camera_id': 2, 'camera': 'Camera 02', 'track_id': 44, 'timestamp': '2026-09-21T10:07:15'},
            {'plate': 'LR60WJZ', 'camera_id': 1, 'camera': 'Camera 01', 'track_id': 81, 'timestamp': '2026-09-21T10:00:10'},
            {'plate': 'LR60WJZ', 'camera_id': 3, 'camera': 'Camera 03', 'track_id': 12, 'timestamp': '2026-09-21T10:03:22'},
        ]

        journey = MultiCameraCorrelationService.correlate(observations)['LR60WJZ']

        self.assertEqual(journey['camera_sequence'], ['Camera 01', 'Camera 03', 'Camera 02'])
        self.assertEqual(journey['first_seen'], '2026-09-21T10:00:10')
        self.assertEqual(journey['last_seen'], '2026-09-21T10:07:15')
        self.assertEqual(journey['visits'][0]['track_ids'], [81])

    def test_intelligence_and_explanation_are_evidence_bound(self):
        journey = MultiCameraCorrelationService.correlate([
            {'plate': 'LR60WJZ', 'camera': 'Camera 02', 'timestamp': '2026-09-21T10:07:15', 'confidence': 0.91},
            {'plate': 'LR60WJZ', 'camera': 'Camera 01', 'timestamp': '2026-09-21T10:00:10', 'confidence': 0.94},
            {'plate': 'LR60WJZ', 'camera': 'Camera 03', 'timestamp': '2026-09-21T10:03:22', 'confidence': 0.90},
        ])['LR60WJZ']

        facts = TrajectoryIntelligenceService.summarize(journey)
        explanation = EvidenceBoundTrajectoryExplainer.explain(facts)

        self.assertEqual(facts['route'], ['Camera 01', 'Camera 03', 'Camera 02'])
        self.assertEqual([item['elapsed_seconds'] for item in facts['transitions']], [192, 233])
        self.assertEqual(facts['average_confidence'], 0.9167)
        self.assertIn('Camera 01', explanation)
        self.assertIn('Camera 03', explanation)
        self.assertNotIn('road', explanation.lower())

    def test_keeps_different_plates_as_separate_journeys(self):
        journeys = MultiCameraCorrelationService.correlate([
            {'plate': 'LR60WJZ', 'camera': 'Camera 01', 'timestamp': '2026-09-21T10:00:10'},
            {'plate': 'TS09AB1234', 'camera': 'Camera 03', 'timestamp': '2026-09-21T10:03:22'},
        ])

        self.assertEqual(set(journeys), {'LR60WJZ', 'TS09AB1234'})

    def test_coalesces_repeated_observations_at_one_camera(self):
        journey = MultiCameraCorrelationService.correlate([
            {'plate': 'LR60WJZ', 'camera': 'Camera 01', 'track_id': 81, 'timestamp': '2026-09-21T10:00:10'},
            {'plate': 'LR60WJZ', 'camera': 'Camera 01', 'track_id': 81, 'timestamp': '2026-09-21T10:00:20'},
            {'plate': 'LR60WJZ', 'camera': 'Camera 01', 'track_id': 81, 'timestamp': '2026-09-21T10:00:30'},
        ])['LR60WJZ']

        self.assertEqual(journey['camera_sequence'], ['Camera 01'])
        self.assertEqual(journey['visits'][0]['observation_count'], 3)
        self.assertEqual(journey['visits'][0]['track_ids'], [81])
