from pathlib import Path

from ultralytics import YOLO


BACKEND_ROOT = Path(__file__).resolve().parent
DATASET_CONFIG = BACKEND_ROOT.parent / 'data' / 'datasets' / 'indian_license_plates' / 'plate_data.yaml'


def main() -> None:
    model = YOLO('yolo11n.pt')
    model.train(
        data=str(DATASET_CONFIG),
        epochs=50,
        imgsz=640,
        batch=8,
        device='cpu',
        workers=2,
        project=str(BACKEND_ROOT / 'runs'),
        name='plate_detector_baseline',
        patience=10,
        seed=42,
        pretrained=True,
        cache=False,
        plots=True,
        verbose=True,
    )
    print('\nTraining complete.')
    print('Best model:')
    print(BACKEND_ROOT / 'runs' / 'plate_detector_baseline' / 'weights' / 'best.pt')


if __name__ == '__main__':
    main()
