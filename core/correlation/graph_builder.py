# core/correlation/graph_builder.py
"""
Entity Relationship Graph Builder
----------------------------------
Constructs a graph of related entities (domains, IPs, emails, etc.)
from normalized OSINT data with weighted edges based on evidence strength.
"""

import logging
import networkx as nx
from typing import List, Dict, Any, Set
from collections import defaultdict
import json

logger = logging.getLogger("core.correlation.graph")


class EntityGraphBuilder:
    """Builds entity relationship graphs from normalized threat data."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.entity_metadata = {}
        
    def build_graph(self, normalized_records: List[Dict[str, Any]]) -> nx.DiGraph:
        """
        Construct entity graph from normalized records.
        
        Args:
            normalized_records: List of normalized OSINT records
            
        Returns:
            NetworkX directed graph with weighted edges
        """
        logger.info(f"Building entity graph from {len(normalized_records)} records")
        
        # Step 1: Extract all entities
        entities_by_type = self._extract_entities(normalized_records)
        
        # Step 2: Add nodes to graph
        self._add_nodes(entities_by_type)
        
        # Step 3: Create relationships
        self._create_relationships(normalized_records, entities_by_type)
        
        # Step 4: Calculate centrality metrics
        self._compute_centrality()
        
        logger.info(f"Graph built: {self.graph.number_of_nodes()} nodes, "
                   f"{self.graph.number_of_edges()} edges")
        
        return self.graph
    
    def _extract_entities(self, records: List[Dict]) -> Dict[str, Set[str]]:
        """Extract unique entities by type."""
        entities = defaultdict(set)
        
        for record in records:
            entity_type = record.get('type', 'unknown')
            indicator = record.get('indicator')
            
            if indicator and indicator != 'unknown':
                entities[entity_type].add(indicator)
                
                # Store metadata
                entity_key = f"{entity_type}:{indicator}"
                self.entity_metadata[entity_key] = {
                    'source': record.get('source'),
                    'confidence': record.get('confidence', 0.5),
                    'timestamp': record.get('timestamp'),
                    'data': record.get('data', {})
                }
        
        logger.debug(f"Extracted {sum(len(v) for v in entities.values())} unique entities")
        return dict(entities)
    
    def _add_nodes(self, entities_by_type: Dict[str, Set[str]]):
        """Add entity nodes to graph with attributes."""
        for entity_type, entity_set in entities_by_type.items():
            for entity in entity_set:
                entity_key = f"{entity_type}:{entity}"
                metadata = self.entity_metadata.get(entity_key, {})
                
                self.graph.add_node(
                    entity,
                    type=entity_type,
                    confidence=metadata.get('confidence', 0.5),
                    source=metadata.get('source', 'unknown'),
                    first_seen=metadata.get('timestamp'),
                    metadata=metadata.get('data', {})
                )
    
    def _create_relationships(self, records: List[Dict], 
                            entities_by_type: Dict[str, Set[str]]):
        """Create edges between related entities."""
        
        # Group records by correlation_hash (if exists)
        correlation_groups = defaultdict(list)
        for record in records:
            corr_hash = record.get('correlation_hash')
            if corr_hash:
                correlation_groups[corr_hash].append(record)
        
        # Create edges within correlation groups
        for corr_hash, group in correlation_groups.items():
            if len(group) < 2:
                continue
                
            # Connect all entities in this correlation group
            for i, record1 in enumerate(group):
                indicator1 = record1.get('indicator')
                if not indicator1 or indicator1 == 'unknown':
                    continue
                    
                for record2 in group[i+1:]:
                    indicator2 = record2.get('indicator')
                    if not indicator2 or indicator2 == 'unknown':
                        continue
                    
                    # Calculate edge weight based on confidence
                    weight = (record1.get('confidence', 0.5) + 
                             record2.get('confidence', 0.5)) / 2
                    
                    # Add bidirectional edges
                    self.graph.add_edge(
                        indicator1, indicator2,
                        weight=weight,
                        relation='correlated',
                        evidence=corr_hash
                    )
                    self.graph.add_edge(
                        indicator2, indicator1,
                        weight=weight,
                        relation='correlated',
                        evidence=corr_hash
                    )
        
        # Create relationships based on data fields
        self._create_semantic_relationships(records)
    
    def _create_semantic_relationships(self, records: List[Dict]):
        """Create edges based on semantic relationships in data."""
        
        for record in records:
            indicator = record.get('indicator')
            if not indicator or indicator == 'unknown':
                continue
                
            data = record.get('data', {})
            
            # Link IPs to domains
            if record.get('type') == 'network_intel':
                domain = data.get('hostname') or data.get('domain')
                if domain and domain in self.graph:
                    self.graph.add_edge(
                        indicator, domain,
                        weight=0.8,
                        relation='resolves_to'
                    )
            
            # Link domains to emails
            if 'email' in data:
                email = data['email']
                if email and email in self.graph:
                    self.graph.add_edge(
                        indicator, email,
                        weight=0.7,
                        relation='associated_with'
                    )
    
    def _compute_centrality(self):
        """Compute centrality metrics for threat prioritization."""
        try:
            # Degree centrality (number of connections)
            degree_cent = nx.degree_centrality(self.graph)
            
            # PageRank (importance based on connections)
            pagerank = nx.pagerank(self.graph, weight='weight')
            
            # Betweenness centrality (bridge between clusters)
            betweenness = nx.betweenness_centrality(self.graph, weight='weight')
            
            # Update node attributes
            for node in self.graph.nodes():
                self.graph.nodes[node]['degree_centrality'] = degree_cent.get(node, 0)
                self.graph.nodes[node]['pagerank'] = pagerank.get(node, 0)
                self.graph.nodes[node]['betweenness'] = betweenness.get(node, 0)
                
        except Exception as e:
            logger.warning(f"Centrality computation failed: {e}")
    
    def get_connected_components(self) -> List[Set[str]]:
        """Return list of connected entity clusters."""
        return list(nx.weakly_connected_components(self.graph))
    
    def export_graph(self, output_path: str):
        """Export graph to JSON format."""
        graph_data = {
            'nodes': [
                {
                    'id': node,
                    **self.graph.nodes[node]
                }
                for node in self.graph.nodes()
            ],
            'edges': [
                {
                    'source': u,
                    'target': v,
                    **self.graph[u][v]
                }
                for u, v in self.graph.edges()
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, default=str, ensure_ascii=False)
        
        logger.info(f"Graph exported to {output_path}")