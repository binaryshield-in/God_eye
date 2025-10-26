# core/correlation/confidence_engine.py
"""
Threat Confidence Scoring Engine
---------------------------------
Calculates threat confidence scores using heuristic rules,
graph topology, and cross-source validation.
"""

import logging
import networkx as nx
from typing import Dict, List, Any
import numpy as np

logger = logging.getLogger("core.correlation.confidence")


class ThreatConfidenceEngine:
    """Computes threat confidence scores for entities."""
    
    # Threat score weights
    WEIGHTS = {
        'base_confidence': 0.3,      # From source trust
        'centrality': 0.25,          # Graph importance
        'cross_validation': 0.25,    # Multiple sources
        'temporal_decay': 0.2        # Data freshness
    }
    
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        self.scores = {}
        
    def compute_scores(self) -> Dict[str, float]:
        """
        Calculate threat confidence score for each entity.
        
        Returns:
            Dict mapping entity ID to confidence score (0-1)
        """
        logger.info("Computing threat confidence scores")
        
        for node in self.graph.nodes():
            score = self._calculate_entity_score(node)
            self.scores[node] = round(score, 3)
        
        logger.info(f"Computed scores for {len(self.scores)} entities")
        return self.scores
    
    def _calculate_entity_score(self, entity: str) -> float:
        """Calculate comprehensive threat score for single entity."""
        node_data = self.graph.nodes[entity]
        
        # Component 1: Base confidence from source
        base_conf = node_data.get('confidence', 0.5)
        
        # Component 2: Centrality score (graph importance)
        centrality_score = self._centrality_score(entity)
        
        # Component 3: Cross-validation (multiple sources)
        cross_val_score = self._cross_validation_score(entity)
        
        # Component 4: Temporal decay (data freshness)
        temporal_score = self._temporal_score(node_data.get('first_seen'))
        
        # Weighted combination
        final_score = (
            self.WEIGHTS['base_confidence'] * base_conf +
            self.WEIGHTS['centrality'] * centrality_score +
            self.WEIGHTS['cross_validation'] * cross_val_score +
            self.WEIGHTS['temporal_decay'] * temporal_score
        )
        
        return min(1.0, max(0.0, final_score))
    
    def _centrality_score(self, entity: str) -> float:
        """Score based on graph centrality metrics."""
        node_data = self.graph.nodes[entity]
        
        # Combine multiple centrality measures
        degree = node_data.get('degree_centrality', 0)
        pagerank = node_data.get('pagerank', 0)
        betweenness = node_data.get('betweenness', 0)
        
        # Normalize pagerank (usually very small values)
        pagerank_normalized = min(1.0, pagerank * 100)
        
        return (degree + pagerank_normalized + betweenness) / 3
    
    def _cross_validation_score(self, entity: str) -> float:
        """Score based on number of corroborating sources."""
        # Count unique sources connected to this entity
        neighbors = list(self.graph.neighbors(entity))
        
        if not neighbors:
            return 0.5  # No validation available
        
        # More connections = higher confidence
        unique_sources = len(set(
            self.graph.nodes[n].get('source') 
            for n in neighbors
        ))
        
        # Normalize: 1 source = 0.5, 3+ sources = 1.0
        return min(1.0, 0.5 + (unique_sources - 1) * 0.25)
    
    def _temporal_score(self, timestamp: str) -> float:
        """Score based on data freshness."""
        if not timestamp:
            return 0.5
        
        try:
            from datetime import datetime, timezone
            ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            age_days = (datetime.now(timezone.utc) - ts).days
            
            # Fresh data (< 7 days) = 1.0
            # Old data (> 365 days) = 0.3
            if age_days <= 7:
                return 1.0
            elif age_days >= 365:
                return 0.3
            else:
                return 1.0 - (age_days / 365) * 0.7
                
        except Exception:
            return 0.5
    
    def get_top_threats(self, n: int = 10) -> List[tuple]:
        """Return top N entities by threat score."""
        sorted_threats = sorted(
            self.scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_threats[:n]
    
    def get_threat_distribution(self) -> Dict[str, int]:
        """Return distribution of threat levels."""
        distribution = {
            'critical': 0,   # >= 0.8
            'high': 0,       # 0.6 - 0.8
            'medium': 0,     # 0.4 - 0.6
            'low': 0         # < 0.4
        }
        
        for score in self.scores.values():
            if score >= 0.8:
                distribution['critical'] += 1
            elif score >= 0.6:
                distribution['high'] += 1
            elif score >= 0.4:
                distribution['medium'] += 1
            else:
                distribution['low'] += 1
        
        return distribution