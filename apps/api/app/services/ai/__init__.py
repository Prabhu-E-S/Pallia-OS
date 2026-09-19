"""AI extraction service package.

Extraction turns a free-form caregiver update (typically a transcript) into a
strict, typed list of candidate observations. Safety is enforced by the
provider contracts in ``prompts.py`` and re-enforced here during validation.
"""

from app.services.ai.extraction import ExtractionResult, extract_from_transcript
from app.services.ai.schemas import ExtractedObservation, ExtractionOutput

__all__ = [
    "ExtractedObservation",
    "ExtractionOutput",
    "ExtractionResult",
    "extract_from_transcript",
]
