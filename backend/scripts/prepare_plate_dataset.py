"""Create a reproducible YOLO train/validation/test layout for plate detection."""

from __future__ import annotations

import argparse
import random
import shutil
from collections import Counter
from pathlib import Path


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
SPLIT_RATIOS = {'train': 0.80, 'val': 0.10, 'test': 0.10}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--dataset-root',
        type=Path,
        default=Path(__file__).resolve().parents[2] / 'data' / 'datasets' / 'indian_license_plates',
    )
    parser.add_argument('--seed', type=int, default=42)
    return parser.parse_args()


def split_names(image_names: list[str], seed: int) -> dict[str, list[str]]:
    shuffled = image_names.copy()
    random.Random(seed).shuffle(shuffled)
    total = len(shuffled)
    train_end = round(total * SPLIT_RATIOS['train'])
    val_end = train_end + round(total * SPLIT_RATIOS['val'])
    return {
        'train': shuffled[:train_end],
        'val': shuffled[train_end:val_end],
        'test': shuffled[val_end:],
    }


def write_data_yaml(dataset_root: Path) -> None:
    dataset_path = dataset_root.as_posix()
    (dataset_root / 'plate_data.yaml').write_text(
        f"path: {dataset_path}\n\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n\n"
        "names:\n"
        "  0: license_plate\n",
        encoding='utf-8',
    )


def main() -> None:
    args = parse_args()
    root = args.dataset_root.resolve()
    image_root = root / 'images'
    label_root = root / 'labels'
    if not image_root.is_dir() or not label_root.is_dir():
        raise FileNotFoundError('Expected source images/ and labels/ directories.')

    source_images = sorted(
        path for path in image_root.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not source_images:
        raise ValueError('No source images were found.')

    source_labels = {path.stem: path for path in label_root.glob('*.txt')}
    image_stems = {path.stem for path in source_images}
    orphan_labels = sorted(set(source_labels) - image_stems)
    if orphan_labels:
        raise ValueError(f'Labels without matching images: {orphan_labels[:5]}')

    destinations = [
        image_root / split for split in SPLIT_RATIOS
    ] + [
        label_root / split for split in SPLIT_RATIOS
    ]
    populated = [path for path in destinations if path.exists() and any(path.iterdir())]
    if populated:
        raise FileExistsError(
            'Split directories already contain data. Remove them manually only if you intend to rebuild. '
            f'Found: {", ".join(str(path) for path in populated)}'
        )

    assignments = split_names([image.name for image in source_images], args.seed)
    seen = [name for names in assignments.values() for name in names]
    if len(seen) != len(set(seen)) or set(seen) != {path.name for path in source_images}:
        raise AssertionError('Split assignment is not a complete non-overlapping partition.')

    image_by_name = {path.name: path for path in source_images}
    totals = Counter()
    negatives = Counter()
    for split, names in assignments.items():
        split_images = image_root / split
        split_labels = label_root / split
        split_images.mkdir(exist_ok=True)
        split_labels.mkdir(exist_ok=True)
        for name in names:
            image = image_by_name[name]
            shutil.copy2(image, split_images / image.name)
            label = source_labels.get(image.stem)
            if label:
                shutil.copy2(label, split_labels / label.name)
            else:
                negatives[split] += 1
            totals[split] += 1

    for split in SPLIT_RATIOS:
        output_images = {path.stem for path in (image_root / split).iterdir() if path.is_file()}
        output_labels = {path.stem for path in (label_root / split).glob('*.txt')}
        if not output_labels.issubset(output_images):
            raise AssertionError(f'{split} contains a label without an image.')

    write_data_yaml(root)
    print(f'Seed: {args.seed}')
    for split in SPLIT_RATIOS:
        label_count = len(list((label_root / split).glob('*.txt')))
        print(f'{split}: images={totals[split]}, labels={label_count}, negatives={negatives[split]}')
    print(f'Wrote: {root / "plate_data.yaml"}')


if __name__ == '__main__':
    main()
