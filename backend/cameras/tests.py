from django.test import TestCase
from rest_framework.test import APIClient

from .models import Camera


class CameraReadApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.camera = Camera.objects.create(
            name='Camera 01', code='camera-01', location_name='Demo District One',
            latitude='17.432600', longitude='78.407100', is_active=True,
        )

    def test_list_and_detail_expose_map_coordinates(self):
        list_response = self.client.get('/api/cameras/')
        detail_response = self.client.get(f'/api/cameras/{self.camera.id}/')

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data[0]['location_name'], 'Demo District One')
        self.assertEqual(str(list_response.data[0]['latitude']), '17.432600')
        self.assertEqual(list_response.data[0]['status'], 'active')
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(str(detail_response.data['longitude']), '78.407100')

    def test_unknown_camera_returns_404(self):
        self.assertEqual(self.client.get('/api/cameras/999999/').status_code, 404)
