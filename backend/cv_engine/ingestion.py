"""Convert CV output into the compact, transport-safe detection API contract."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Mapping


def build_detection_payload(
    result: Mapping[str, Any], *, camera_id: int, timestamp: datetime | str
) -> dict[str, Any]:
    """Build an API payload without coupling CV stages to Django persistence.

    OCR confidence is intentionally used as ``plate_confidence``: the value
    measures confidence in the recognized registration text, whereas the plate
    detector confidence only measures whether a box looks like a plate.
    """
    ocr = result.get('ocr') or {}
    vehicle = result.get('vehicle') or {}
    plate = str(ocr.get('normalized_text') or '').strip()
    if not plate:
        raise ValueError('A normalized OCR plate is required for ingestion.')
    if not isinstance(camera_id, int) or isinstance(camera_id, bool) or camera_id <= 0:
        raise ValueError('camera_id must be a positive integer.')
    if isinstance(timestamp, datetime):
        timestamp = timestamp.isoformat().replace('+00:00', 'Z')
    if not isinstance(timestamp, str) or not timestamp:
        raise ValueError('timestamp must be an ISO 8601 string or datetime.')
    if vehicle.get('confidence') is None:
        raise ValueError('Vehicle confidence is required for ingestion.')
    if ocr.get('confidence') is None:
        raise ValueError('OCR confidence is required for ingestion.')

    def confidence(value: Any) -> float:
        normalized = Decimal(str(value)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        if not Decimal('0') <= normalized <= Decimal('1'):
            raise ValueError('Confidence must be between 0 and 1.')
        return float(normalized)

    return {
        'plate': plate,
        'camera_id': camera_id,
        'timestamp': timestamp,
        'plate_confidence': confidence(ocr['confidence']),
        'vehicle_confidence': confidence(vehicle['confidence']),
        'vehicle_type': vehicle.get('vehicle_type', ''),
    }
