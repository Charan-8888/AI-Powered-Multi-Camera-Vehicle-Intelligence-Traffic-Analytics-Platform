from datetime import datetime, timezone

from django.test import TestCase
from rest_framework.test import APIClient

from cameras.models import Camera
from detections.models import Detection
from .models import Vehicle
from .serializers import VehicleSerializer


class VehicleSerializerTests(TestCase):
    def test_plate_number_is_normalized(self):
        serializer = VehicleSerializer(data={'plate_number': 'ka 01 ab 1234'})

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['plate_number'], 'KA01AB1234')


class VehicleIntelligenceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.camera_one = Camera.objects.create(name='Camera 01', code='camera-01', location_name='Demo District One', latitude='17.432600', longitude='78.407100')
        self.camera_three = Camera.objects.create(name='Camera 03', code='camera-03', location_name='Demo District Three', latitude='17.439900', longitude='78.398800')
        self.vehicle = Vehicle.objects.create(plate_number='TS09AB1234', vehicle_type='car')
        for camera, timestamp in (
            (self.camera_three, '2026-09-21T10:17:41+00:00'),
            (self.camera_one, '2026-09-21T10:15:23+00:00'),
            (self.camera_one, '2026-09-21T10:16:00+00:00'),
            (self.camera_three, '2026-09-21T10:20:08+00:00'),
        ):
            Detection.objects.create(
                camera=camera,
                vehicle=self.vehicle,
                detected_at=datetime.fromisoformat(timestamp),
                plate_confidence='0.9400',
                vehicle_confidence='0.9100',
            )

    def test_list_detail_and_normalized_search(self):
        list_response = self.client.get('/api/vehicles/')
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data['count'], 1)
        self.assertEqual(list_response.data['results'][0]['detection_count'], 4)

        detail_response = self.client.get(f'/api/vehicles/{self.vehicle.id}/')
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data['plate'], 'TS09AB1234')

        search_response = self.client.get('/api/vehicles/search/?plate=ts-09 ab 1234')
        self.assertEqual(search_response.status_code, 200)
        self.assertEqual(search_response.data['id'], self.vehicle.id)

    def test_unknown_plate_returns_404(self):
        response = self.client.get('/api/vehicles/search/?plate=UNKNOWN123')
        self.assertEqual(response.status_code, 404)

    def test_trajectory_reuses_ordering_and_camera_coalescing(self):
        response = self.client.get(f'/api/vehicles/{self.vehicle.id}/trajectory/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['trajectory']['camera_sequence'], ['Camera 01', 'Camera 03'])
        self.assertEqual(response.data['trajectory']['total_detections'], 4)
        self.assertEqual(response.data['detections'][0]['camera']['name'], 'Camera 01')
        self.assertEqual(response.data['detections'][0]['camera']['location_name'], 'Demo District One')
        self.assertEqual(str(response.data['detections'][0]['camera']['latitude']), '17.432600')

# Create your tests here.
