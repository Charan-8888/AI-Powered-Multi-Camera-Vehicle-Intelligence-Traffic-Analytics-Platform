# ANPR Models

This directory holds locally downloaded model weights for the ANPR CV engine.

## Required model

- `plate_detector.pt`

The selected model must detect vehicle number plates as bounding boxes inside
vehicle crops and support Ultralytics YOLO inference.

## Selection requirements

- License compatible with the SIH prototype.
- Suitable for Indian number plates where possible.
- Documented class mapping and source provenance.
- Acceptable model size and inference speed on the target hardware.
# Conditionally promoted MVP detector

`plate_detector.pt` is the locally promoted YOLO11n candidate checkpoint. Its
held-out test evaluation and known limitations are recorded in
`plate_detector_metadata.json`. It is suitable for the MVP pipeline, not a
production robustness claim: the corrected test set contains no genuine
no-plate scenes.
