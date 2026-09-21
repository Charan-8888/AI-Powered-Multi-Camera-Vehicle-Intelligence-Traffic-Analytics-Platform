from django.db import models


class Vehicle(models.Model):
    plate_number = models.CharField(max_length=16, unique=True, db_index=True)
    vehicle_type = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=50, blank=True)
    first_seen_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['plate_number']

    def __str__(self):
        return self.plate_number

# Create your models here.
