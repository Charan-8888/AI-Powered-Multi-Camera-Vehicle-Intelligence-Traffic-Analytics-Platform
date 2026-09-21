from rest_framework import serializers

from .models import Vehicle
from .normalization import normalize_plate


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'first_seen_at', 'last_seen_at')

    def validate_plate_number(self, value):
        normalized = normalize_plate(value)
        if len(normalized) < 6 or len(normalized) > 16:
            raise serializers.ValidationError('Enter a valid normalized vehicle registration number.')
        return normalized


class VehicleReadSerializer(serializers.ModelSerializer):
    plate = serializers.CharField(source='plate_number', read_only=True)
    first_seen = serializers.DateTimeField(source='first_seen_at', read_only=True)
    last_seen = serializers.DateTimeField(source='last_seen_at', read_only=True)
    detection_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Vehicle
        fields = ('id', 'plate', 'vehicle_type', 'first_seen', 'last_seen', 'detection_count')
