from pathlib import Path

import cv2

from cv_engine.plate_detector import PlateDetector


IMAGE_PATH = Path(__file__).resolve().parent / 'venv' / 'Lib' / 'site-packages' / 'ultralytics' / 'assets' / 'bus.jpg'


def main():
    image = cv2.imread(str(IMAGE_PATH))
    if image is None:
        raise FileNotFoundError(f'Could not read image: {IMAGE_PATH}')

    plates = PlateDetector().detect(image)
    print(f'Candidate plates: {len(plates)}')
    for index, plate in enumerate(plates, start=1):
        print(f"{index}. bbox={plate['bbox']} | area={plate['area']} | aspect_ratio={plate['aspect_ratio']}")


if __name__ == '__main__':
    main()
