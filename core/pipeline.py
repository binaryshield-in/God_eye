# pipeline.py
"""
Main Orchestrator for Normalization & Intelligence Pipeline
"""

import json
import logging
from core.normalizer import DataNormalizer
from core.resolver import resolve_entities
from core.confidence import compute_confidence
from core.correlator import correlate_entities
from core.enrichment import enrich_data

logger = logging.getLogger('GodEye')


class NormalizationPipeline:
    """Production-grade normalization pipeline orchestrator."""

    def __init__(self, schema_path: str = None):
        self.normalizer = DataNormalizer(schema_path)

    def run(self, raw_data: dict, query_type: str) -> dict:
        """
        Execute full normalization and enrichment pipeline.
        
        Args:
            raw_data: Full collector response from main.py
            query_type: Type of query (domain, ip, etc.)
        
        Returns:
            Dict with normalized, entities, and analytics
        """
        try:
            # Step 1: Normalize
            normalized = self.normalizer.normalize(raw_data, query_type)
            
            if not normalized:
                logger.warning("No data normalized")
                return {
                    "normalized": [],
                    "entities": [],
                    "analytics": {"count": 0, "status": "no_data"}
                }

            # Step 2: Resolve entities
            entities = resolve_entities(normalized)
            
            # Step 3: Enrich
            enriched = enrich_data(entities)
            
            # Step 4: Correlate
            correlated = correlate_entities(enriched)
            
            # Step 5: Compute final confidence
            scored = compute_confidence(normalized)

            return {
                "normalized": scored,
                "entities": correlated,
                "analytics": {
                    "count": len(scored),
                    "entities_found": len(correlated),
                    "status": "success"
                }
            }

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
            return {
                "normalized": [],
                "entities": [],
                "analytics": {"error": str(e), "status": "failed"}
            }
        
# Add to core/pipeline.py

from core.correlation import (
    EntityGraphBuilder,
    ThreatConfidenceEngine,
    SemanticEmbedder,
    AnalyticsGenerator
)

class NormalizationPipeline:
    """Enhanced pipeline with AI correlation."""
    
    def __init__(self, schema_path: str = None):
        self.normalizer = DataNormalizer(schema_path)
        
    def run(self, raw_data: dict, query_type: str) -> dict:
        """Execute full pipeline with AI correlation."""
        try:
            # Step 1: Normalize
            normalized = self.normalizer.normalize(raw_data, query_type)
            
            if not normalized:
                logger.warning("No data normalized")
                return self._empty_response()
            
            # Step 2: Build entity graph
            graph_builder = EntityGraphBuilder()
            graph = graph_builder.build_graph(normalized)
            graph_builder.export_graph("results/entity_graph.json")
            
            # Step 3: Compute threat scores
            confidence_engine = ThreatConfidenceEngine(graph)
            scores = confidence_engine.compute_scores()
            
            # Step 4: Generate embeddings
            embedder = SemanticEmbedder()
            embeddings = embedder.generate_embeddings(normalized)
            embedder.save_embeddings("results/embeddings.npz")
            
            # Step 5: Generate analytics
            analytics_gen = AnalyticsGenerator(graph, scores, embeddings)
            analytics = analytics_gen.generate_analytics("results/analytics.json")
            
            return {
                "normalized": normalized,
                "graph": graph,
                "scores": scores,
                "analytics": analytics
            }
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
            return self._empty_response()
    
    def _empty_response(self):
        return {
            "normalized": [],
            "analytics": {"status": "failed"}
        }