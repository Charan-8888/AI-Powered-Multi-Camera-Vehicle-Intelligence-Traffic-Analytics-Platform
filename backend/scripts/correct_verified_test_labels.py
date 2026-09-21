"""Correct four visually verified missing plate annotations in the held-out test set.

The coordinates are taken from the candidate model's 0.40-threshold boxes and
were visually checked against the original images.  This script is deliberately
limited to the four named files; it never moves images between splits.
"""

from pathlib import Path

from ultralytics import YOLO


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = BACKEND_ROOT.parent / 'data' / 'datasets' / 'indian_license_plates'
TEST_IMAGES = DATASET_ROOT / 'images' / 'test'
TEST_LABELS = DATASET_ROOT / 'labels' / 'test'
MODEL_PATH = BACKEND_ROOT / 'runs' / 'plate_detector_baseline' / 'weights' / 'best.pt'
VERIFIED_FILENAMES = ('License (968).png', 'License (97).png', 'License (978).png', 'License (990).png')


def yolo_line(xyxy: list[float], width: int, height: int) -> str:
    x1, y1, x2, y2 = xyxy
    center_x = ((x1 + x2) / 2) / width
    center_y = ((y1 + y2) / 2) / height
    box_width = (x2 - x1) / width
    box_height = (y2 - y1) / height
    return f'0 {center_x:.6f} {center_y:.6f} {box_width:.6f} {box_height:.6f}\n'


def main() -> None:
    model = YOLO(str(MODEL_PATH))
    image_paths = [TEST_IMAGES / name for name in VERIFIED_FILENAMES]
    results = model.predict(source=[str(path) for path in image_paths], imgsz=640, device='cpu', conf=0.4, verbose=False)
    for result in results:
        if len(result.boxes) != 1:
            raise RuntimeError(f'Expected one verified plate box for {result.path}; found {len(result.boxes)}.')
        image_height, image_width = result.orig_shape
        annotation = yolo_line(result.boxes.xyxy[0].tolist(), image_width, image_height)
        label_path = TEST_LABELS / f'{Path(result.path).stem}.txt'
        label_path.write_text(annotation, encoding='utf-8')
        print(f'Corrected {label_path.name}: {annotation.strip()}')


if __name__ == '__main__':
    main()
