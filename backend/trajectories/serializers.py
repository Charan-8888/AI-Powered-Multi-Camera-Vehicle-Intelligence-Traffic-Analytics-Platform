from rest_framework import serializers

from .models import Trajectory


class TrajectorySerializer(serializers.ModelSerializer):
    plate_number = serializers.CharField(source='vehicle.plate_number', read_only=True)

    class Meta:
        model = Trajectory
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'plate_number')
