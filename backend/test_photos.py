"""
test_photos.py — Run the full ANPR pipeline (Vehicle detect → Plate detect → OCR)
on every image inside  'testing photos/'  and print a detailed report.

Usage (from the backend/ directory with venv active):
    python test_photos.py
"""

import os
import sys
import time
from pathlib import Path

# ── Point Ultralytics / Paddle at the project's runtime folder ───────────────
BACKEND = Path(__file__).resolve().parent
os.environ.setdefault('YOLO_CONFIG_DIR', str(BACKEND / 'runtime'))
os.environ.setdefault('PADDLE_PDX_CACHE_HOME', str(BACKEND / 'runtime' / 'paddle'))

import cv2
import numpy as np

# ── Paths ─────────────────────────────────────────────────────────────────────
PHOTOS_DIR   = BACKEND.parent / 'testing photos'
VEHICLE_MODEL = str(BACKEND / 'yolo11n.pt')
PLATE_MODEL   = str(BACKEND / 'models' / 'plate_detector.pt')
OUTPUT_DIR    = BACKEND.parent / 'testing photos' / 'output'
OUTPUT_DIR.mkdir(exist_ok=True)

SUPPORTED = {'.png', '.jpg', '.jpeg', '.bmp', '.webp'}

# ─────────────────────────────────────────────────────────────────────────────
def separator(char='─', width=65):
    print(char * width)

def header(text):
    separator('═')
    print(f'  {text}')
    separator('═')

# ─────────────────────────────────────────────────────────────────────────────
def load_models():
    """Load all three models and return them."""
    from ultralytics import YOLO
    from cv_engine.ocr import PlateOCR

    header('Loading models…')
    t0 = time.time()

    print('  [1/3]  Vehicle detector   →  yolo11n.pt (COCO pre-trained)')
    vehicle_model = YOLO(VEHICLE_MODEL)

    print('  [2/3]  Plate detector     →  models/plate_detector.pt (custom YOLO11n)')
    plate_model = YOLO(PLATE_MODEL)

    print('  [3/3]  PaddleOCR          →  English OCR (downloaded on first run)')
    ocr = PlateOCR()

    print(f'\n  ✓ All models ready in {time.time()-t0:.1f}s')
    return vehicle_model, plate_model, ocr


# ─────────────────────────────────────────────────────────────────────────────
VEHICLE_CLASSES = {2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}
VEHICLE_CONF    = 0.30   # lower threshold so we catch tricky angles
PLATE_CONF      = 0.25   # lower to handle blurry crops

def run_pipeline(image_path: Path, vehicle_model, plate_model, ocr):
    """Run the full pipeline on one image. Returns a result dict."""
    frame = cv2.imread(str(image_path))
    if frame is None:
        return {'error': 'Could not open image', 'path': image_path}

    h, w = frame.shape[:2]
    annotated = frame.copy()
    results = []

    # ── Stage 1: Vehicle detection ─────────────────────────────────────────
    vehicle_detections = []
    for yolo_result in vehicle_model(frame, conf=VEHICLE_CONF, verbose=False):
        if yolo_result.boxes is None:
            continue
        for box in yolo_result.boxes:
            cid = int(box.cls[0])
            if cid not in VEHICLE_CLASSES:
                continue
            vehicle_detections.append({
                'vehicle_type': VEHICLE_CLASSES[cid],
                'confidence':   float(box.conf[0]),
                'bbox':         [int(v) for v in box.xyxy[0].tolist()],
            })

    # ── If no vehicle found, try treating whole image as a vehicle crop ────
    # (handles the case where photo IS the plate crop already)
    if not vehicle_detections:
        vehicle_detections = [{
            'vehicle_type': 'unknown',
            'confidence':   1.0,
            'bbox':         [0, 0, w, h],
            'fallback':     True,
        }]

    # ── Stage 2 & 3: Plate detection + OCR per vehicle ────────────────────
    for veh in vehicle_detections:
        x1, y1, x2, y2 = veh['bbox']
        x1, x2 = max(0, x1), min(w, x2)
        y1, y2 = max(0, y1), min(h, y2)
        vehicle_crop = frame[y1:y2, x1:x2]
        if vehicle_crop.size == 0:
            continue

        # Draw vehicle box
        is_fallback = veh.get('fallback', False)
        if not is_fallback:
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (56, 189, 248), 2)
            cv2.putText(annotated,
                        f"{veh['vehicle_type']} {veh['confidence']:.0%}",
                        (x1, max(y1-8, 0)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (56, 189, 248), 2)

        plates_found = []
        for pres in plate_model(vehicle_crop, conf=PLATE_CONF, verbose=False):
            if pres.boxes is None:
                continue
            for pbox in pres.boxes:
                px1, py1, px2, py2 = [int(v) for v in pbox.xyxy[0].tolist()]
                plate_crop = vehicle_crop[py1:py2, px1:px2]
                if plate_crop.size == 0:
                    continue

                ocr_out = ocr.recognize(plate_crop)

                # Absolute coords for annotation
                ax1, ay1 = x1 + px1, y1 + py1
                ax2, ay2 = x1 + px2, y1 + py2
                cv2.rectangle(annotated, (ax1, ay1), (ax2, ay2), (52, 211, 153), 3)

                label = ocr_out['normalized_text'] or '(unreadable)'
                conf_label = f"{ocr_out['confidence']:.0%}"
                cv2.putText(annotated, f"{label}  {conf_label}",
                            (ax1, ay1 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (52, 211, 153), 2)

                plates_found.append({
                    'plate_bbox':        [ax1, ay1, ax2, ay2],
                    'plate_conf':        float(pbox.conf[0]),
                    'ocr_text':          ocr_out['text'],
                    'ocr_normalized':    ocr_out['normalized_text'],
                    'ocr_confidence':    ocr_out['confidence'],
                })

        results.append({
            'vehicle':  veh,
            'plates':   plates_found,
            'fallback': is_fallback,
        })

    # ── Save annotated image ───────────────────────────────────────────────
    out_path = OUTPUT_DIR / f'result_{image_path.name}'
    cv2.imwrite(str(out_path), annotated)

    return {
        'path':       image_path,
        'shape':      (w, h),
        'vehicles':   results,
        'out_path':   out_path,
    }


# ─────────────────────────────────────────────────────────────────────────────
def print_result(res, idx):
    separator()
    print(f'  IMAGE {idx}: {res["path"].name}')
    print(f'  Size  : {res["shape"][0]}×{res["shape"][1]} px')
    separator()

    if 'error' in res:
        print(f'  ✗ ERROR: {res["error"]}')
        return

    total_plates = sum(len(v['plates']) for v in res['vehicles'])
    vehicles = [v for v in res['vehicles'] if not v.get('fallback')]
    print(f'  Vehicles detected : {len(vehicles)}')
    print(f'  Plates detected   : {total_plates}')
    print()

    for vi, vdata in enumerate(res['vehicles']):
        v = vdata['vehicle']
        if vdata.get('fallback'):
            print(f'  ℹ️  No vehicle box found — treated entire image as crop')
        else:
            print(f'  Vehicle {vi+1}: {v["vehicle_type"].upper()}  '
                  f'(confidence {v["confidence"]:.1%})')

        if not vdata['plates']:
            print('       └─ No plate detected in this vehicle crop')
        else:
            for pi, p in enumerate(vdata['plates']):
                raw   = p['ocr_text'] or '(empty)'
                norm  = p['ocr_normalized'] or '(empty)'
                pconf = p['plate_conf']
                oconf = p['ocr_confidence']
                status = '✓ READ' if norm and len(norm) >= 4 else '⚠ PARTIAL'
                print(f'       └─ Plate {pi+1}:  {status}')
                print(f'             OCR raw text   : "{raw}"')
                print(f'             Normalized      : "{norm}"')
                print(f'             Plate det. conf : {pconf:.1%}')
                print(f'             OCR conf        : {oconf:.1%}')
        print()

    print(f'  📁 Annotated image saved → {res["out_path"].name}')


# ─────────────────────────────────────────────────────────────────────────────
def main():
    photos = sorted(
        p for p in PHOTOS_DIR.iterdir()
        if p.suffix.lower() in SUPPORTED and p.parent == PHOTOS_DIR
    )

    if not photos:
        print(f'No images found in: {PHOTOS_DIR}')
        sys.exit(1)

    vehicle_model, plate_model, ocr = load_models()

    header(f'Running ANPR pipeline on {len(photos)} image(s)')
    print(f'  Input  : {PHOTOS_DIR}')
    print(f'  Output : {OUTPUT_DIR}')
    print()

    all_results = []
    for idx, photo in enumerate(photos, 1):
        print(f'  Processing {idx}/{len(photos)}: {photo.name} …', end='', flush=True)
        t0 = time.time()
        res = run_pipeline(photo, vehicle_model, plate_model, ocr)
        elapsed = time.time() - t0
        print(f' done ({elapsed:.1f}s)')
        all_results.append(res)

    print()
    header('RESULTS')
    for idx, res in enumerate(all_results, 1):
        print_result(res, idx)

    # ── Summary ───────────────────────────────────────────────────────────
    separator('═')
    print('  SUMMARY')
    separator('═')
    total_plates = sum(
        len(v['plates']) for r in all_results if 'vehicles' in r
        for v in r['vehicles']
    )
    total_reads = sum(
        1 for r in all_results if 'vehicles' in r
        for v in r['vehicles']
        for p in v['plates']
        if p['ocr_normalized'] and len(p['ocr_normalized']) >= 4
    )
    print(f'  Images processed  : {len(all_results)}')
    print(f'  Plates detected   : {total_plates}')
    print(f'  Plates read (≥4ch): {total_reads}')
    print(f'  Annotated images  : {OUTPUT_DIR}')
    separator('═')


if __name__ == '__main__':
    main()
