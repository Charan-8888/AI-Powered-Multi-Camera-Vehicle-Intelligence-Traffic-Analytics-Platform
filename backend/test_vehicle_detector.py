from pathlib import Path

import cv2

from cv_engine.detector import VehicleDetector


IMAGE_PATH = Path(__file__).resolve().parent / 'venv' / 'Lib' / 'site-packages' / 'ultralytics' / 'assets' / 'bus.jpg'


def main():
    frame = cv2.imread(str(IMAGE_PATH))
    if frame is None:
        raise FileNotFoundError(f'Could not read image: {IMAGE_PATH}')

    detections = VehicleDetector().detect(frame)
    print(f'Detected vehicles: {len(detections)}')
    for index, detection in enumerate(detections, start=1):
        print(
            f"{index}. {detection['vehicle_type']} | "
            f"confidence={detection['confidence']:.2f} | bbox={detection['bbox']}"
        )


if __name__ == '__main__':
    main()
