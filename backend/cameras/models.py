from django.db import models


class Camera(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.SlugField(max_length=64, unique=True)
    location_name = models.CharField(max_length=120, blank=True)
    location_description = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.code})'

# Create your models here.
