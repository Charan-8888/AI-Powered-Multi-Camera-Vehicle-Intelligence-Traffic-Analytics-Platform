from rest_framework import serializers

from .models import Camera


class CameraSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Camera
        fields = (
            'id', 'name', 'code', 'location_name', 'location_description', 'latitude',
            'longitude', 'is_active', 'status', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_status(self, instance):
        return 'active' if instance.is_active else 'inactive'
