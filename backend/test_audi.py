"""
Test the Audi screenshot from the user's upload.
This image is a 1999x1092 screenshot of video processing software
showing an Audi with plate 'KI-52.99E'.
We'll test via the scan API and save the annotated result.
"""
import requests, base64
from pathlib import Path

# The user's screenshot - look for it in downloads or testing photos
# Try to find it
import os
possible = [
    r'D:\ANPR-MVP\ANPR-MVP\testing photos',
    r'C:\Users\araba\Downloads',
    r'C:\Users\araba\Desktop',
]

found = []
for folder in possible:
    p = Path(folder)
    if p.exists():
        for f in p.iterdir():
            if f.suffix.lower() in {'.png', '.jpg', '.jpeg'} and f.stat().st_size > 100_000:
                found.append(f)

print('Candidate images found:')
for i, f in enumerate(found):
    print(f'  [{i}] {f.name}  ({f.stat().st_size//1024} KB)')

if found:
    # Test the largest image (most likely to be the Audi screenshot)
    target = max(found, key=lambda f: f.stat().st_size)
    print(f'\nTesting: {target.name}')
    with open(target, 'rb') as f:
        r = requests.post('http://127.0.0.1:8000/api/scan/image/', files={'image': f})
    data = r.json()
    print(f'HTTP {r.status_code} | detections={data["total_detections"]} | fallback={data["fallback_mode"]}')
    for i, d in enumerate(data.get('detections', [])):
        print(f'  Plate {i+1}: {d["plate"]}  (plate_conf={d["plate_confidence"]:.0%}, ocr={d["ocr_confidence"]:.0%})')

    # Save annotated
    out = Path(r'D:\ANPR-MVP\ANPR-MVP\testing photos\output_v2\audi_result.jpg')
    b64 = data['annotated_image'].split(',', 1)[1]
    out.write_bytes(base64.b64decode(b64))
    print(f'Annotated image saved: {out}')
