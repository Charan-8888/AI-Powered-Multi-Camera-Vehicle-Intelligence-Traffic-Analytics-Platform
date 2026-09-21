from rest_framework import viewsets

from .models import Detection
from .serializers import DetectionIngestionSerializer, DetectionSerializer


class DetectionViewSet(viewsets.ModelViewSet):
    queryset = Detection.objects.select_related('camera', 'vehicle').all()
    serializer_class = DetectionSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return DetectionIngestionSerializer
        return DetectionSerializer

# Create your views here.
