"""
URL configuration for config project.
"""

from datetime import timedelta

from django.contrib import admin
from django.db.models import Count, Max
from django.urls import include, path
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter

from cameras.models import Camera
from cameras.views import CameraViewSet
from detections.models import Detection
from detections.views import DetectionViewSet
from trajectories.models import Trajectory
from trajectories.views import TrajectoryViewSet
from vehicles.models import Vehicle
from vehicles.views import VehicleViewSet
from scan.views import scan_image


router = DefaultRouter()
router.register('cameras', CameraViewSet, basename='camera')
router.register('vehicles', VehicleViewSet, basename='vehicle')
router.register('detections', DetectionViewSet, basename='detection')
router.register('trajectories', TrajectoryViewSet, basename='trajectory')


def _traffic_level(count):
    if count >= 100:
        return 'HIGH'
    if count >= 30:
        return 'MODERATE'
    return 'LOW'


@api_view(['GET'])
def dashboard_stats(request):
    """Headline KPIs for the city dashboard.

    Real data  : vehicles, detections, cameras, trajectories.
    Demo data  : active_alerts, traffic_status  (clearly marked).
    """
    total_detections = Detection.objects.count()
    active_cameras   = Camera.objects.filter(is_active=True).count()
    offline_cameras  = Camera.objects.filter(is_active=False).count()
    total_vehicles   = Vehicle.objects.count()
    total_trajectories = Trajectory.objects.count()

    # --- DEMO: derive traffic status from recent detection volume ---
    cutoff = timezone.now() - timedelta(hours=1)
    recent_count = Detection.objects.filter(detected_at__gte=cutoff).count()
    traffic_status = _traffic_level(recent_count * 10)   # scale for demo realism

    # --- DEMO: 1 alert per offline camera + 1 if high traffic ---
    active_alerts = offline_cameras + (1 if traffic_status == 'HIGH' else 0)

    return Response({
        # REAL
        'total_vehicles':    total_vehicles,
        'unique_vehicles':   total_vehicles,      # plate_number is UNIQUE
        'total_detections':  total_detections,
        'total_trajectories': total_trajectories,
        'active_cameras':    active_cameras,
        'offline_cameras':   offline_cameras,
        # DEMO / SIMULATED
        'active_alerts':     active_alerts,
        'traffic_status':    traffic_status,
        # Legacy keys kept for backward-compat
        'vehicles':          total_vehicles,
        'cameras':           active_cameras + offline_cameras,
        'detections':        total_detections,
        'trajectories':      total_trajectories,
    })


@api_view(['GET'])
def city_intelligence(request):
    """City-level intelligence feed.

    recent_detections  REAL
    camera_list        REAL (counts) + DEMO (traffic_level label)
    area_traffic       REAL (counts) + DEMO (level, peak_period)
    alerts             DEMO (deterministic from real data patterns)
    """

    # ── Recent detections (REAL) ─────────────────────────────────
    recent_qs = (
        Detection.objects
        .select_related('camera', 'vehicle')
        .order_by('-detected_at')[:12]
    )
    recent_detections = [
        {
            'id': d.id,
            'plate':              d.vehicle.plate_number,
            'camera_name':        d.camera.name,
            'location':           d.camera.location_name or d.camera.name,
            'timestamp':          d.detected_at,
            'plate_confidence':   d.plate_confidence,
            'vehicle_confidence': d.vehicle_confidence,
        }
        for d in recent_qs
    ]

    # ── Camera list with detection counts (REAL) ──────────────────
    cameras_qs = (
        Camera.objects
        .annotate(
            detection_count=Count('detections'),
            last_detection=Max('detections__detected_at'),
        )
        .order_by('name')
    )

    camera_list = [
        {
            'id':              c.id,
            'name':            c.name,
            'code':            c.code,
            'location':        c.location_name or c.name,
            'latitude':        c.latitude,
            'longitude':       c.longitude,
            'is_active':       c.is_active,
            'status':          'ONLINE' if c.is_active else 'OFFLINE',
            'detection_count': c.detection_count,
            'last_detection':  c.last_detection,
            'traffic_level':   _traffic_level(c.detection_count),  # DETERMINISTIC
        }
        for c in cameras_qs
    ]

    # ── Area traffic (REAL counts, DEMO level label) ──────────────
    area_map = {}
    for c in cameras_qs:
        area = c.location_name or c.name
        if area not in area_map:
            area_map[area] = {
                'area':            area,
                'camera_count':    0,
                'detection_count': 0,
                'vehicle_ids':     set(),
            }
        area_map[area]['camera_count']    += 1
        area_map[area]['detection_count'] += c.detection_count

    for row in Detection.objects.select_related('camera').values('camera__location_name', 'vehicle_id'):
        area = row['camera__location_name'] or 'Unknown'
        area_map.setdefault(area, {
            'area': area, 'camera_count': 0, 'detection_count': 0, 'vehicle_ids': set(),
        })['vehicle_ids'].add(row['vehicle_id'])

    area_traffic = []
    for area, data in area_map.items():
        count = data['detection_count']
        area_traffic.append({
            'area':            area,
            'camera_count':    data['camera_count'],
            'detection_count': count,
            'unique_vehicles': len(data.get('vehicle_ids', set())),
            'traffic_level':   _traffic_level(count),   # DETERMINISTIC
            'peak_period':     '08:00–10:00' if count > 0 else 'N/A',  # DEMO
        })
    area_traffic.sort(key=lambda x: x['detection_count'], reverse=True)

    # ── Alerts (DEMO — deterministic from real patterns) ──────────
    alerts = []
    for cam in [c for c in camera_list if not c['is_active']]:
        alerts.append({
            'id':       f'offline-{cam["id"]}',
            'severity': 'HIGH',
            'type':     'CAMERA_OFFLINE',
            'title':    f'Camera offline: {cam["name"]}',
            'detail':   f'{cam["location"]} has been inactive. Check network connection.',
            'source':   cam['name'],
            'is_demo':  True,
        })

    for area_data in [a for a in area_traffic if a['traffic_level'] == 'HIGH'][:3]:
        alerts.append({
            'id':       f'traffic-{area_data["area"]}',
            'severity': 'MEDIUM',
            'type':     'HIGH_TRAFFIC',
            'title':    f'High traffic: {area_data["area"]}',
            'detail':   (
                f'{area_data["detection_count"]} total detections at this zone. '
                'Consider traffic diversion measures.'
            ),
            'source':   area_data['area'],
            'is_demo':  True,
        })

    if not alerts:
        alerts.append({
            'id':       'system-ok',
            'severity': 'LOW',
            'type':     'SYSTEM_OK',
            'title':    'All systems nominal',
            'detail':   'No active alerts detected. All cameras are reporting normally.',
            'source':   'System Monitor',
            'is_demo':  True,
        })

    return Response({
        'recent_detections': recent_detections,
        'camera_list':       camera_list,
        'area_traffic':      area_traffic,
        'alerts':            alerts,
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/dashboard/stats/',  dashboard_stats,    name='dashboard-stats'),
    path('api/dashboard/city/',   city_intelligence,  name='city-intelligence'),
    path('api/scan/image/',       scan_image,         name='scan-image'),
    path('api/', include(router.urls)),
]
