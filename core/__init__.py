# core/__init__.py
"""
Core Intelligence Pipeline for GodEye
------------------------------------
Initializes all normalization, enrichment, and correlation components.
"""

from .normalizer import normalize_data, DataNormalizer
from .resolver import resolve_entities
from .confidence import compute_confidence
from .correlator import correlate_entities
from .enrichment import enrich_data
from .pipeline import NormalizationPipeline  # ✅ FIXED: Import class instead of function

__all__ = [
    "normalize_data",
    "DataNormalizer",
    "resolve_entities",
    "compute_confidence",
    "correlate_entities",
    "enrich_data",
    "NormalizationPipeline"  # ✅ Export the class
]