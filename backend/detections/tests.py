from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from cameras.models import Camera
from cv_engine.ingestion import build_detection_payload
from vehicles.models import Vehicle

from .models import Detection


class DetectionApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.camera = Camera.objects.create(name='Main Gate', code='main-gate')
        self.vehicle = Vehicle.objects.create(plate_number='KA01AB1234')
        Detection.objects.create(
            camera=self.camera,
            vehicle=self.vehicle,
            detected_at=timezone.now(),
            vehicle_confidence='0.9876',
            plate_confidence='0.9123',
        )

    def test_detection_list_includes_vehicle_and_camera_context(self):
        response = self.client.get('/api/detections/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['plate_number'], 'KA01AB1234')
        self.assertEqual(response.data[0]['camera_name'], 'Main Gate')

    def test_dashboard_returns_entity_counts(self):
        response = self.client.get('/api/dashboard/stats/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            'vehicles': 1,
            'cameras': 1,
            'detections': 1,
            'trajectories': 0,
        })

    def ingestion_payload(self, **overrides):
        payload = {
            'plate': 'ts-09 ab 1234',
            'camera_id': self.camera.id,
            'timestamp': '2026-09-21T10:15:23Z',
            'plate_confidence': 0.94,
            'vehicle_confidence': 0.91,
            'vehicle_type': 'car',
        }
        payload.update(overrides)
        return payload

    def test_post_creates_normalized_vehicle_and_detection(self):
        response = self.client.post('/api/detections/', self.ingestion_payload(), format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['plate_number'], 'TS09AB1234')
        self.assertEqual(response.data['camera_name'], 'Main Gate')
        self.assertEqual(response.data['vehicle_details']['plate_number'], 'TS09AB1234')
        vehicle = Vehicle.objects.get(plate_number='TS09AB1234')
        self.assertEqual(vehicle.vehicle_type, 'car')
        self.assertTrue(Detection.objects.filter(vehicle=vehicle).exists())

    def test_post_reuses_existing_vehicle(self):
        existing = Vehicle.objects.create(plate_number='TS09AB1234')

        response = self.client.post('/api/detections/', self.ingestion_payload(), format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['vehicle'], existing.id)
        self.assertEqual(Vehicle.objects.filter(plate_number='TS09AB1234').count(), 1)

    def test_post_rejects_blank_plate_invalid_camera_timestamp_and_confidence(self):
        invalid_payloads = (
            self.ingestion_payload(plate='   '),
            self.ingestion_payload(camera_id=999999),
            self.ingestion_payload(timestamp='not-a-timestamp'),
            self.ingestion_payload(plate_confidence=1.01),
            self.ingestion_payload(vehicle_confidence=-0.01),
        )

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post('/api/detections/', payload, format='json')
                self.assertEqual(response.status_code, 400)

    def test_fake_cv_result_can_be_persisted_through_detection_api(self):
        cv_result = {
            'vehicle': {'vehicle_type': 'car', 'confidence': 0.91},
            'plate': {'confidence': 0.94},
            'ocr': {'normalized_text': 'TS09AB1234', 'confidence': 0.97},
        }
        payload = build_detection_payload(
            cv_result, camera_id=self.camera.id, timestamp='2026-09-21T10:15:23Z'
        )

        response = self.client.post('/api/detections/', payload, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['plate_number'], 'TS09AB1234')
        self.assertEqual(str(response.data['plate_confidence']), '0.9700')
        self.assertEqual(Detection.objects.filter(vehicle__plate_number='TS09AB1234').count(), 1)

# Create your tests here.
