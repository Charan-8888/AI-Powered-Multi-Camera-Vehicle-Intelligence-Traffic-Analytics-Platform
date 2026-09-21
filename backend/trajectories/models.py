from django.db import models


class Trajectory(models.Model):
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.CASCADE, related_name='trajectories')
    started_at = models.DateTimeField(db_index=True)
    ended_at = models.DateTimeField(db_index=True)
    detection_count = models.PositiveIntegerField(default=0)
    route = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-started_at']
        indexes = [models.Index(fields=['vehicle', 'started_at'], name='trajectory_vehicle_time_idx')]

    def __str__(self):
        return f'{self.vehicle}: {self.started_at:%Y-%m-%d %H:%M} → {self.ended_at:%Y-%m-%d %H:%M}'

# Create your models here.
