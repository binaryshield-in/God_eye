# core/correlation/__init__.py
"""
AI Correlation Engine for GodEye
---------------------------------
Transforms normalized OSINT data into structured threat intelligence
with entity graphs, confidence scores, and semantic embeddings.
"""

from .graph_builder import EntityGraphBuilder
from .confidence_engine import ThreatConfidenceEngine
from .embeddings import SemanticEmbedder
from .analytics import AnalyticsGenerator

__all__ = [
    "EntityGraphBuilder",
    "ThreatConfidenceEngine", 
    "SemanticEmbedder",
    "AnalyticsGenerator"
]