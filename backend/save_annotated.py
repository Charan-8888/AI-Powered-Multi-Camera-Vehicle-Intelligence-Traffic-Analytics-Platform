"""Save annotated images from the improved scan endpoint for visual review."""
import requests, base64, json
from pathlib import Path

IMGS = [
    ('motion_blur', r'D:\ANPR-MVP\ANPR-MVP\testing photos\Screenshot 2026-09-21 215020.png'),
    ('blur',        r'D:\ANPR-MVP\ANPR-MVP\testing photos\Screenshot 2026-09-21 215017.png'),
    ('full_car',    r'D:\ANPR-MVP\ANPR-MVP\testing photos\Screenshot 2026-09-21 215024.png'),
]
OUT = Path(r'D:\ANPR-MVP\ANPR-MVP\testing photos\output_v2')
OUT.mkdir(exist_ok=True)

for name, path in IMGS:
    with open(path, 'rb') as f:
        r = requests.post('http://127.0.0.1:8000/api/scan/image/', files={'image': f})
    data = r.json()
    b64  = data['annotated_image'].split(',', 1)[1]
    out  = OUT / f'{name}.jpg'
    out.write_bytes(base64.b64decode(b64))
    print(f'Saved {out.name}  —  {data["total_detections"]} valid detection(s)')
