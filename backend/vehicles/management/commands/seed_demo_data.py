from datetime import datetime, timedelta, timezone

from django.core.management.base import BaseCommand

from cameras.models import Camera
from detections.models import Detection
from vehicles.models import Vehicle


class Command(BaseCommand):
    help = 'Create development-only ANPR dashboard demo records.'

    def handle(self, *args, **options):
        camera_details = (
            ('Camera 01', 'Demo District One', '17.401100', '78.401100'),
            ('Camera 02', 'Demo District Two', '17.405200', '78.409200'),
            ('Camera 03', 'Demo District Three', '17.412300', '78.397300'),
            ('Camera 04', 'Demo District Four', '17.418400', '78.414400'),
        )
        cameras = []
        for index, (name, location_name, latitude, longitude) in enumerate(camera_details, start=1):
            camera, _ = Camera.objects.update_or_create(
                name=name,
                defaults={
                    'code': f'camera-{index:02d}', 'location_name': location_name,
                    'latitude': latitude, 'longitude': longitude, 'is_active': True,
                },
            )
            cameras.append(camera)
        for offset, plate in enumerate(('TS09AB1234', 'TS10CD5678', 'AP09EF4321')):
            vehicle, _ = Vehicle.objects.get_or_create(plate_number=plate, defaults={'vehicle_type': 'car'})
            start = datetime(2026, 9, 21, 10, 15, tzinfo=timezone.utc) + timedelta(minutes=offset)
            for index, camera in enumerate((cameras[0], cameras[2], cameras[1])):
                detected_at = start + timedelta(minutes=index * 2)
                Detection.objects.get_or_create(camera=camera, vehicle=vehicle, detected_at=detected_at, defaults={'plate_confidence': '0.9400', 'vehicle_confidence': '0.9100'})
        self.stdout.write(self.style.SUCCESS('Development demo data is ready.'))
