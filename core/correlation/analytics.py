# core/correlation/analytics.py
"""
Analytics Aggregation Module
-----------------------------
Generates comprehensive analytics.json output combining
graph analysis, confidence scores, and embeddings.
"""

import logging
import json
from typing import Dict, Any, List
from datetime import datetime, timezone
import networkx as nx
import numpy as np

logger = logging.getLogger("core.correlation.analytics")


class AnalyticsGenerator:
    """Aggregates all correlation outputs into analytics.json."""
    
    def __init__(self, graph: nx.DiGraph, scores: Dict[str, float], 
                 embeddings: Dict[str, np.ndarray]):
        self.graph = graph
        self.scores = scores
        self.embeddings = embeddings
        
    def generate_analytics(self, output_path: str = "results/analytics.json"):
        """
        Generate comprehensive analytics report.
        
        Creates analytics.json with:
        - summary: aggregate statistics
        - entities: detailed entity information
        - scores: threat confidence scores
        - embeddings: semantic vectors (first 10D for preview)
        - relationships: graph connections
        """
        logger.info("Generating analytics report")
        
        analytics = {
            'metadata': self._generate_metadata(),
            'summary': self._generate_summary(),
            'threat_distribution': self._get_threat_distribution(),
            'top_threats': self._get_top_threats(),
            'entities': self._generate_entity_details(),
            'relationships': self._generate_relationships(),
            'clusters': self._detect_clusters(),
            'embeddings_preview': self._generate_embeddings_preview()
        }
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analytics, f, indent=2, default=self._json_serializer, ensure_ascii=False)
        
        logger.info(f"Analytics saved to {output_path}")
        return analytics
    
    def _generate_metadata(self) -> Dict[str, Any]:
        """Generate report metadata."""
        return {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'version': '1.0',
            'pipeline_stage': 'correlation',
            'total_entities': self.graph.number_of_nodes(),
            'total_relationships': self.graph.number_of_edges()
        }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate aggregate statistics."""
        if not self.scores:
            avg_confidence = 0
        else:
            avg_confidence = sum(self.scores.values()) / len(self.scores)
        
        entity_types = {}
        for node in self.graph.nodes():
            node_type = self.graph.nodes[node].get('type', 'unknown')
            entity_types[node_type] = entity_types.get(node_type, 0) + 1
        
        return {
            'total_entities': self.graph.number_of_nodes(),
            'total_connections': self.graph.number_of_edges(),
            'average_confidence': round(avg_confidence, 3),
            'entity_types': entity_types,
            'embedding_dimension': len(next(iter(self.embeddings.values()))) if self.embeddings else 0
        }
    
    def _get_threat_distribution(self) -> Dict[str, int]:
        """Get threat level distribution."""
        distribution = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
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
    
    def _get_top_threats(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get top N threats."""
        sorted_threats = sorted(
            self.scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:n]
        
        return [
            {
                'entity': entity,
                'confidence': score,
                'type': self.graph.nodes[entity].get('type'),
                'connections': self.graph.degree(entity)
            }
            for entity, score in sorted_threats
        ]
    
    def _generate_entity_details(self) -> List[Dict[str, Any]]:
        """Generate detailed entity information."""
        entities = []
        
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            
            entity = {
                'id': node,
                'type': node_data.get('type'),
                'confidence': self.scores.get(node, 0.5),
                'source': node_data.get('source'),
                'first_seen': node_data.get('first_seen'),
                'connections': self.graph.degree(node),
                'degree_centrality': node_data.get('degree_centrality', 0),
                'pagerank': node_data.get('pagerank', 0),
                'metadata': node_data.get('metadata', {})
            }
            
            entities.append(entity)
        
        return entities
    
    def _generate_relationships(self) -> List[Dict[str, Any]]:
        """Generate relationship mappings."""
        relationships = []
        
        for source, target in self.graph.edges():
            edge_data = self.graph[source][target]
            
            relationships.append({
                'source': source,
                'target': target,
                'weight': edge_data.get('weight', 0.5),
                'relation': edge_data.get('relation', 'related'),
                'evidence': edge_data.get('evidence')
            })
        
        return relationships
    
    def _detect_clusters(self) -> List[Dict[str, Any]]:
        """Detect entity clusters/communities."""
        try:
            # Find weakly connected components
            components = list(nx.weakly_connected_components(self.graph))
            
            clusters = []
            for i, component in enumerate(components):
                if len(component) < 2:  # Skip isolated nodes
                    continue
                
                cluster_nodes = list(component)
                avg_score = sum(self.scores.get(n, 0) for n in cluster_nodes) / len(cluster_nodes)
                
                clusters.append({
                    'cluster_id': i,
                    'size': len(cluster_nodes),
                    'entities': cluster_nodes,
                    'average_confidence': round(avg_score, 3)
                })
            
            return clusters
            
        except Exception as e:
            logger.warning(f"Cluster detection failed: {e}")
            return []
    
    def _generate_embeddings_preview(self) -> Dict[str, List[float]]:
        """Generate embedding preview (first 10 dimensions)."""
        preview = {}
        
        for entity, vector in list(self.embeddings.items())[:20]:  # Limit to 20 entities
            preview[entity] = vector[:10].tolist()  # First 10 dimensions
        
        return preview
    
    @staticmethod
    def _json_serializer(obj):
        """Handle non-serializable objects."""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        return str(obj)