from pathlib import Path

import cv2

from cv_engine.detector import VehicleDetector
from cv_engine.ocr import PlateOCR
from cv_engine.plate_detector import PlateDetector
from cv_engine.processor import VideoProcessor


IMAGE_PATH = Path(__file__).resolve().parent / 'venv' / 'Lib' / 'site-packages' / 'ultralytics' / 'assets' / 'bus.jpg'


def main():
    frame = cv2.imread(str(IMAGE_PATH))
    if frame is None:
        raise FileNotFoundError(f'Could not read image: {IMAGE_PATH}')

    processor = VideoProcessor(VehicleDetector(), PlateDetector(), PlateOCR())
    results = processor.process_frame(frame)

    print(f'Pipeline results: {len(results)}')
    for index, result in enumerate(results, start=1):
        vehicle = result['vehicle']
        plate = result['plate']
        ocr_result = result['ocr']
        print(f'\nResult {index}')
        print('-------------')
        print('Vehicle:', vehicle['vehicle_type'])
        print('Vehicle confidence:', vehicle['confidence'])
        print('Vehicle bbox:', vehicle['bbox'])
        print('Plate bbox:', plate['bbox'])
        print('OCR text:', ocr_result['text'])
        print('Normalized plate:', ocr_result['normalized_text'])
        print('OCR confidence:', ocr_result['confidence'])


if __name__ == '__main__':
    main()
