"""
cv_engine/plate_preprocess.py

Plate crop preprocessing and OCR post-processing utilities used by the
scan pipeline to improve accuracy on small, blurry, or low-contrast crops.

Three problems solved here:
  1. Watermark false positives  — BLUR / MOTIONBLUR / MOSAIC labels on demo images
     are filtered out by the word-blacklist before the result reaches the caller.
  2. 7 ↔ T (and other digit/alpha) OCR confusions — corrected with positional rules
     and regex pattern matching for common licence-plate formats.
  3. Small / blurry crops       — pre-processed through upscale → denoise → CLAHE →
     sharpen before being handed to PaddleOCR.
"""

from __future__ import annotations

import re

import cv2
import numpy as np

# ── Watermark word blacklist ──────────────────────────────────────────────────
# These strings appear as overlay labels in sample/demo images and should never
# be treated as valid plate text.
_WATERMARKS: frozenset[str] = frozenset({
    'BLUR', 'BLURRED',
    'MOTION', 'MOTIONBLUR', 'MOTION BLUR',
    'MOSAIC', 'MOSAICED',
    'WATERMARK', 'WATERMARKED',
    'SAMPLE', 'DEMO', 'TEST', 'EXAMPLE',
    'PREVIEW', 'REDACTED', 'CENSORED',
})


def is_watermark(normalized_text: str) -> bool:
    """Return True when the OCR output looks like a watermark, not a plate.

    Checks both the raw text (with spaces stripped) and the original text
    against the blacklist.
    """
    t = (normalized_text or '').upper()
    return t in _WATERMARKS or t.replace(' ', '') in _WATERMARKS


# ── Plate validity filter ─────────────────────────────────────────────────────
def is_valid_plate_crop(px1: int, py1: int, px2: int, py2: int,
                         crop_w: int, crop_h: int) -> bool:
    """Return False when the bounding box cannot be a real number plate.

    Licence plates are always wider than tall (aspect ratio 1.3 – 7.0) and
    must have at least 800 pixels of area (≈ 40×20 min) to be OCR-readable.

    Note: We deliberately do NOT use an area-fraction check here because on
    large (1080p+) images the plate can occupy well under 0.5 % of the frame.
    The watermark-word blacklist handles text-overlay false positives instead.
    """
    pw = px2 - px1
    ph = py2 - py1
    if ph <= 0 or pw <= 0:
        return False

    aspect = pw / ph
    area   = pw * ph

    return 1.3 <= aspect <= 7.0 and area >= 800


# ── OCR character correction ──────────────────────────────────────────────────
# PaddleOCR confuses visually similar digits and letters, especially at low
# resolution.  We apply deterministic corrections after reading the raw text.

def correct_plate(text: str) -> str:
    """Apply character-level corrections for common ANPR OCR mistakes.

    Rules applied (in order):
      R1  Leading T followed by letters then digits  →  replace T with 7
          e.g. TYEA627  →  7YEA627
      R2  'T' adjacent to a digit on either side     →  7
          e.g. T1, 3T, 1T2                           →  71, 37, 172
      R3  'O' sandwiched between two digits          →  0
          e.g. 1O2                                   →  102
    """
    if not text:
        return text

    t = text.upper()

    # R1 — leading T + 1-4 letters + 2-4 digits  (e.g. TYEA627 → 7YEA627)
    if re.match(r'^T[A-Z]{1,4}\d{2,4}$', t):
        t = '7' + t[1:]

    # R2 — T flanked by a digit
    # Process character by character so we can look at neighbours
    chars  = list(t)
    result = []
    for i, ch in enumerate(chars):
        prev_digit = bool(result) and result[-1].isdigit()
        next_digit = (i < len(chars) - 1) and chars[i + 1].isdigit()

        if ch == 'T' and (prev_digit or next_digit):
            result.append('7')
        else:
            result.append(ch)

    # R3 — O between digits
    joined = ''.join(result)
    joined = re.sub(r'(?<=\d)O(?=\d)', '0', joined)

    return joined


# ── Image preprocessing ───────────────────────────────────────────────────────
_SHARPEN_KERNEL = np.array([[0, -1,  0],
                              [-1,  5, -1],
                              [0, -1,  0]], dtype=np.float32)


def preprocess_plate_crop(crop, target_height: int = 80):
    """Upscale → denoise → CLAHE → sharpen a plate crop for PaddleOCR.

    Returns a BGR image at *at least* ``target_height`` pixels tall.
    If the input is already large enough, only contrast enhancement and
    sharpening are applied.
    """
    if crop is None or crop.size == 0:
        return crop

    h, w = crop.shape[:2]

    # 1. Upscale small crops with bicubic interpolation
    if h < target_height:
        scale = target_height / h
        new_w = max(int(w * scale), 1)
        crop  = cv2.resize(crop, (new_w, target_height),
                           interpolation=cv2.INTER_CUBIC)

    # 2. Work in grayscale for denoising and contrast steps
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) \
           if len(crop.shape) == 3 else crop.copy()

    # 3. Non-local means denoising (conservative: h=8)
    gray = cv2.fastNlMeansDenoising(gray, h=8,
                                     templateWindowSize=7,
                                     searchWindowSize=21)

    # 4. CLAHE contrast enhancement
    clahe    = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
    enhanced = clahe.apply(gray)

    # 5. Unsharp mask / sharpening
    blurred   = cv2.GaussianBlur(enhanced, (3, 3), 0)
    sharpened = cv2.addWeighted(enhanced, 1.5, blurred, -0.5, 0)
    sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)

    # 6. Return as BGR so PaddleOCR is happy
    return cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)


# ── Multi-attempt OCR ─────────────────────────────────────────────────────────
def best_ocr(ocr, original_crop) -> dict:
    """Run OCR on the original crop and a preprocessed version.

    Returns the result with the highest confidence after applying character
    corrections.  The watermark check is NOT applied here — the caller
    decides what to do with watermark hits so it can annotate the image
    correctly (e.g. draw a red/orange box instead of a green one).
    """
    def _run(crop) -> dict:
        try:
            return ocr.recognize(crop)
        except Exception:
            return {'text': '', 'normalized_text': '', 'confidence': 0.0}

    r_orig = _run(original_crop)
    r_pre  = _run(preprocess_plate_crop(original_crop))

    # Pick the higher-confidence result
    best = r_pre if r_pre.get('confidence', 0) > r_orig.get('confidence', 0) \
           else r_orig

    # Apply character corrections to the normalized text
    raw_normalized = best.get('normalized_text', '')
    corrected      = correct_plate(raw_normalized)

    out = dict(best)
    if corrected != raw_normalized:
        out['normalized_text']    = corrected
        out['correction_applied'] = True
        out['original_ocr']       = raw_normalized    # keep for debugging
    else:
        out['correction_applied'] = False

    return out
