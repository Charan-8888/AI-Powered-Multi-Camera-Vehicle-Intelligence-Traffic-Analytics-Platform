import requests

IMGS = [
    ('Motion blur (Image 1)', r'D:\ANPR-MVP\ANPR-MVP\testing photos\Screenshot 2026-09-21 215020.png'),
    ('Blur (Image 2)',         r'D:\ANPR-MVP\ANPR-MVP\testing photos\Screenshot 2026-09-21 215017.png'),
    ('Full car (Image 3)',     r'D:\ANPR-MVP\ANPR-MVP\testing photos\Screenshot 2026-09-21 215024.png'),
]

URL = 'http://127.0.0.1:8000/api/scan/image/'

for label, path in IMGS:
    print(f'\n{"="*60}')
    print(f'  {label}')
    print(f'{"="*60}')
    with open(path, 'rb') as f:
        r = requests.post(URL, files={'image': f})
    data = r.json()
    print(f'  HTTP {r.status_code}  |  detections={data["total_detections"]}  |  fallback={data["fallback_mode"]}')
    if not data['detections']:
        print('  (No valid plates detected — watermarks/invalid shapes filtered)')
    for i, d in enumerate(data['detections']):
        plate    = d.get('plate', '?')
        pc       = d.get('plate_confidence', 0)
        oc       = d.get('ocr_confidence', 0)
        corrected= d.get('correction_applied', False)
        orig     = d.get('original_ocr', '')
        print(f'  Plate {i+1}: {plate}  '
              f'(plate_conf={pc:.0%}, ocr={oc:.0%}'
              f'{f", corrected from [{orig}]" if corrected else ""})')
