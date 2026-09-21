from rest_framework import serializers

from cameras.models import Camera
from .models import Detection
from vehicles.normalization import normalize_plate
from vehicles.models import Vehicle


class VehicleSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ('id', 'plate_number', 'vehicle_type', 'first_seen_at', 'last_seen_at')


class DetectionIngestionSerializer(serializers.ModelSerializer):
    """Accept the compact, model-agnostic payload emitted by ``cv_engine``."""

    plate = serializers.CharField(write_only=True, trim_whitespace=True)
    camera_id = serializers.PrimaryKeyRelatedField(
        source='camera', queryset=Camera.objects.all()
    )
    timestamp = serializers.DateTimeField(source='detected_at')
    plate_confidence = serializers.DecimalField(
        max_digits=5, decimal_places=4, min_value=0, max_value=1, required=False, allow_null=True
    )
    vehicle_confidence = serializers.DecimalField(
        max_digits=5, decimal_places=4, min_value=0, max_value=1
    )
    vehicle_type = serializers.CharField(required=False, allow_blank=True, write_only=True)
    vehicle = serializers.PrimaryKeyRelatedField(read_only=True)
    vehicle_details = VehicleSummarySerializer(source='vehicle', read_only=True)
    plate_number = serializers.CharField(source='vehicle.plate_number', read_only=True)
    camera_name = serializers.CharField(source='camera.name', read_only=True)

    class Meta:
        model = Detection
        fields = (
            'id', 'plate', 'plate_number', 'camera_id', 'camera_name', 'vehicle',
            'vehicle_details', 'timestamp', 'vehicle_confidence', 'plate_confidence',
            'vehicle_type', 'created_at',
        )
        read_only_fields = ('id', 'created_at', 'plate_number', 'camera_name', 'vehicle', 'vehicle_details')

    def validate_plate(self, value):
        normalized = normalize_plate(value)
        if not normalized:
            raise serializers.ValidationError('Plate must contain at least one letter or number.')
        return normalized

    def create(self, validated_data):
        plate = validated_data.pop('plate')
        vehicle_type = validated_data.pop('vehicle_type', '')
        detected_at = validated_data['detected_at']

        vehicle, created = Vehicle.objects.get_or_create(
            plate_number=plate,
            defaults={
                'vehicle_type': vehicle_type,
                'first_seen_at': detected_at,
                'last_seen_at': detected_at,
            },
        )

        updates = []
        if vehicle.first_seen_at is None or detected_at < vehicle.first_seen_at:
            vehicle.first_seen_at = detected_at
            updates.append('first_seen_at')
        if vehicle.last_seen_at is None or detected_at > vehicle.last_seen_at:
            vehicle.last_seen_at = detected_at
            updates.append('last_seen_at')
        if not created and vehicle_type and not vehicle.vehicle_type:
            vehicle.vehicle_type = vehicle_type
            updates.append('vehicle_type')
        if updates:
            vehicle.save(update_fields=updates + ['updated_at'])

        return Detection.objects.create(vehicle=vehicle, **validated_data)


class DetectionSerializer(serializers.ModelSerializer):
    plate_number = serializers.CharField(source='vehicle.plate_number', read_only=True)
    camera_name = serializers.CharField(source='camera.name', read_only=True)

    class Meta:
        model = Detection
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'plate_number', 'camera_name')
