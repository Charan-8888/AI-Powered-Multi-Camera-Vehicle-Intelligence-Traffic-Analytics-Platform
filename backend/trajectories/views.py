from django.shortcuts import render

from rest_framework import viewsets

from .models import Trajectory
from .serializers import TrajectorySerializer


class TrajectoryViewSet(viewsets.ModelViewSet):
    queryset = Trajectory.objects.select_related('vehicle').all()
    serializer_class = TrajectorySerializer

# Create your views here.
