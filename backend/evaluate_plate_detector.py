"""Evaluate the plate detector only on the held-out test split."""

from pathlib import Path

from ultralytics import YOLO


BACKEND_ROOT = Path(__file__).resolve().parent
MODEL_PATH = BACKEND_ROOT / 'runs' / 'plate_detector_baseline' / 'weights' / 'best.pt'
DATA_PATH = BACKEND_ROOT.parent / 'data' / 'datasets' / 'indian_license_plates' / 'plate_data.yaml'
TEST_IMAGES = DATA_PATH.parent / 'images' / 'test'
TEST_LABELS = DATA_PATH.parent / 'labels' / 'test'
OUTPUT_ROOT = BACKEND_ROOT / 'runs'


def negative_image_paths() -> list[Path]:
    """Return test images that intentionally have no label file."""
    return sorted(path for path in TEST_IMAGES.iterdir() if not (TEST_LABELS / f'{path.stem}.txt').exists())


def main() -> None:
    model = YOLO(str(MODEL_PATH))
    metrics = model.val(
        data=str(DATA_PATH), split='test', imgsz=640, batch=8, device='cpu',
        workers=0, cache=False, plots=True, verbose=True,
        project=str(OUTPUT_ROOT), name='plate_detector_test', exist_ok=True,
    )
    negatives = negative_image_paths()
    false_positives = []
    if negatives:
        predictions = model.predict(
            source=[str(path) for path in negatives], imgsz=640, device='cpu',
            conf=0.001, verbose=False,
        )
        false_positives = [
            {
                'image': Path(result.path).name,
                'detections': len(result.boxes),
                'max_confidence': round(float(result.boxes.conf.max()), 5) if len(result.boxes) else None,
            }
            for result in predictions
            if len(result.boxes)
        ]
    print('\n=== TEST SET RESULTS ===')
    print(f'Precision:  {metrics.box.mp:.5f}')
    print(f'Recall:     {metrics.box.mr:.5f}')
    print(f'mAP50:      {metrics.box.map50:.5f}')
    print(f'mAP50-95:   {metrics.box.map:.5f}')
    print(f'Negative test images: {len(negatives)}')
    print(f'False positives on negatives: {len(false_positives)}')
    for result in false_positives:
        print(f"  {result['image']}: {result['detections']} detection(s), max confidence {result['max_confidence']}")


if __name__ == '__main__':
    main()
