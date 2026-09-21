from django.db import models


class Detection(models.Model):
    camera = models.ForeignKey('cameras.Camera', on_delete=models.PROTECT, related_name='detections')
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.PROTECT, related_name='detections')
    detected_at = models.DateTimeField(db_index=True)
    vehicle_confidence = models.DecimalField(max_digits=5, decimal_places=4)
    plate_confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    image_path = models.CharField(max_length=500, blank=True)
    plate_crop_path = models.CharField(max_length=500, blank=True)
    bounding_box = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['vehicle', 'detected_at'], name='detection_vehicle_time_idx'),
            models.Index(fields=['camera', 'detected_at'], name='detection_camera_time_idx'),
        ]

    def __str__(self):
        return f'{self.vehicle} at {self.camera} on {self.detected_at:%Y-%m-%d %H:%M:%S}'

# Create your models here.
