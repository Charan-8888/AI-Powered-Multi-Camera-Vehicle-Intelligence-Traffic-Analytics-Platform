from django.db.models import Count

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from .models import Vehicle
from .normalization import normalize_plate
from .serializers import VehicleReadSerializer, VehicleSerializer
from trajectories.services import TrajectoryService


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.annotate(detection_count=Count('detections'))
    serializer_class = VehicleSerializer

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve', 'search'):
            return VehicleReadSerializer
        return VehicleSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return Response({
            'count': queryset.count(),
            'results': self.get_serializer(queryset, many=True).data,
        })

    @action(detail=False, methods=['get'])
    def search(self, request):
        plate = request.query_params.get('plate', '')
        normalized = normalize_plate(plate)
        if not normalized:
            raise ValidationError({'plate': 'Provide a plate containing letters or numbers.'})
        try:
            vehicle = self.get_queryset().get(plate_number=normalized)
        except Vehicle.DoesNotExist as error:
            raise NotFound('Vehicle not found.') from error
        return Response(self.get_serializer(vehicle).data)

    @action(detail=True, methods=['get'])
    def trajectory(self, request, pk=None):
        vehicle = self.get_object()
        records = vehicle.detections.select_related('camera').order_by('detected_at')
        trajectory_input = [
            {
                'plate': vehicle.plate_number,
                'camera': detection.camera.name,
                'camera_data': {
                    'id': detection.camera.id,
                    'name': detection.camera.name,
                    'location_name': detection.camera.location_name,
                    'latitude': detection.camera.latitude,
                    'longitude': detection.camera.longitude,
                },
                'timestamp': detection.detected_at,
                'plate_confidence': detection.plate_confidence,
                'vehicle_confidence': detection.vehicle_confidence,
            }
            for detection in records
        ]
        result = TrajectoryService.build_trajectory(trajectory_input).get(vehicle.plate_number)
        detections = [] if result is None else [
            {
                'camera': item['camera_data'],
                'timestamp': item['timestamp'],
                'plate_confidence': item['plate_confidence'],
                'vehicle_confidence': item['vehicle_confidence'],
            }
            for item in result['detections']
        ]
        trajectory = None if result is None else {
            key: result[key]
            for key in ('first_seen', 'last_seen', 'total_detections', 'camera_sequence')
        }
        return Response({
            'vehicle': {
                'id': vehicle.id,
                'plate': vehicle.plate_number,
                'vehicle_type': vehicle.vehicle_type,
            },
            'trajectory': trajectory,
            'detections': detections,
        })

# Create your views here.
