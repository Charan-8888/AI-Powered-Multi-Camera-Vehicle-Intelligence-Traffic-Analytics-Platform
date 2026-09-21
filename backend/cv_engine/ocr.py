import os
import re
from pathlib import Path

# Keep downloaded Paddle models and configuration under the project runtime directory.
os.environ.setdefault('PADDLE_PDX_CACHE_HOME', str(Path(__file__).resolve().parent.parent / 'runtime' / 'paddle'))

from paddleocr import PaddleOCR


class PlateOCR:
    """Read a plate crop with PaddleOCR and normalize its registration text."""

    def __init__(self) -> None:
        self.ocr = PaddleOCR(
            lang='en',
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            # Avoid a Windows oneDNN/PIR runtime limitation during inference.
            enable_mkldnn=False,
        )

    @staticmethod
    def normalize_plate(text: str) -> str:
        """Normalize whitespace and punctuation from a recognized registration number."""
        return re.sub(r'[^A-Z0-9]', '', (text or '').upper())

    def recognize(self, plate_crop) -> dict[str, object]:
        """Return the highest-confidence text recognized in one plate image."""
        empty = {'text': '', 'normalized_text': '', 'confidence': 0.0}
        if plate_crop is None or plate_crop.size == 0:
            return empty

        best_text, best_confidence = '', 0.0
        for result in self.ocr.predict(plate_crop):
            data = result.json() if callable(getattr(result, 'json', None)) else getattr(result, 'json', result)
            if not isinstance(data, dict):
                continue
            result_data = data.get('res', data)
            for text, score in zip(result_data.get('rec_texts', []), result_data.get('rec_scores', [])):
                confidence = float(score)
                if confidence > best_confidence:
                    best_text, best_confidence = text, confidence

        return {
            'text': best_text,
            'normalized_text': self.normalize_plate(best_text),
            'confidence': best_confidence,
        }
