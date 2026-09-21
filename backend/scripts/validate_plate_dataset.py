"""Report split integrity and known-positive label coverage for the plate dataset."""

from pathlib import Path


DATASET_ROOT = Path(__file__).resolve().parents[2] / 'data' / 'datasets' / 'indian_license_plates'
SPLITS = ('train', 'val', 'test')


def main() -> None:
    total_images = total_labels = 0
    for split in SPLITS:
        images = list((DATASET_ROOT / 'images' / split).glob('*.*'))
        labels = list((DATASET_ROOT / 'labels' / split).glob('*.txt'))
        missing_label_images = [image.name for image in images if not (DATASET_ROOT / 'labels' / split / f'{image.stem}.txt').exists()]
        total_images += len(images)
        total_labels += len(labels)
        print(f'{split}: {len(images)} images, {len(labels)} label files, {len(missing_label_images)} unlabeled')
        if missing_label_images:
            print(f'  Unlabeled: {", ".join(sorted(missing_label_images))}')
    print(f'Total: {total_images} images, {total_labels} label files')
    if total_images != 2083:
        raise SystemExit('Unexpected image count.')


if __name__ == '__main__':
    main()
