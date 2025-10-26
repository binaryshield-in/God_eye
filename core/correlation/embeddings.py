# core/correlation/embeddings.py
"""
Semantic Embeddings Generator
------------------------------
Generates 384D semantic vectors using sentence-transformers
for AI-powered similarity analysis and clustering.
"""

import logging
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("core.correlation.embeddings")


class SemanticEmbedder:
    """Generates semantic embeddings for threat intelligence."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize embedding model.
        
        Args:
            model_name: HuggingFace model (default: 384D embeddings)
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embeddings = {}
        
    def generate_embeddings(self, normalized_records: List[Dict[str, Any]]) -> Dict[str, np.ndarray]:
        """
        Generate embeddings for all entities.
        
        Args:
            normalized_records: Normalized OSINT data
            
        Returns:
            Dict mapping entity ID to 384D embedding vector
        """
        logger.info(f"Generating embeddings for {len(normalized_records)} records")
        
        # Prepare text representations
        entity_texts = {}
        for record in normalized_records:
            indicator = record.get('indicator')
            if not indicator or indicator == 'unknown':
                continue
            
            # Create semantic representation
            text = self._create_semantic_text(record)
            entity_texts[indicator] = text
        
        # Batch encode for efficiency
        if entity_texts:
            indicators = list(entity_texts.keys())
            texts = list(entity_texts.values())
            
            embeddings = self.model.encode(
                texts,
                batch_size=32,
                show_progress_bar=True,
                convert_to_numpy=True
            )
            
            self.embeddings = dict(zip(indicators, embeddings))
        
        logger.info(f"Generated {len(self.embeddings)} embeddings")
        return self.embeddings
    
    def _create_semantic_text(self, record: Dict[str, Any]) -> str:
        """Create semantic text representation of entity."""
        parts = []
        
        # Entity type and indicator
        entity_type = record.get('type', 'unknown')
        indicator = record.get('indicator', '')
        parts.append(f"{entity_type}: {indicator}")
        
        # Source information
        source = record.get('source', '')
        if source:
            parts.append(f"source: {source}")
        
        # Data fields
        data = record.get('data', {})
        for key, value in data.items():
            if value and isinstance(value, (str, int, float)):
                parts.append(f"{key}: {value}")
        
        return " | ".join(parts)
    
    def compute_similarity_matrix(self) -> np.ndarray:
        """Compute cosine similarity matrix between all embeddings."""
        from sklearn.metrics.pairwise import cosine_similarity
        
        if not self.embeddings:
            return np.array([])
        
        embedding_matrix = np.array(list(self.embeddings.values()))
        similarity = cosine_similarity(embedding_matrix)
        
        logger.debug(f"Similarity matrix shape: {similarity.shape}")
        return similarity
    
    def find_similar_entities(self, entity: str, top_k: int = 5) -> List[tuple]:
        """
        Find top-k most similar entities.
        
        Returns:
            List of (entity_id, similarity_score) tuples
        """
        if entity not in self.embeddings:
            return []
        
        query_embedding = self.embeddings[entity]
        similarities = []
        
        for other_entity, other_embedding in self.embeddings.items():
            if other_entity == entity:
                continue
            
            # Cosine similarity
            similarity = np.dot(query_embedding, other_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(other_embedding)
            )
            similarities.append((other_entity, float(similarity)))
        
        # Sort and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def save_embeddings(self, output_path: str):
        """Save embeddings to NumPy file."""
        if not self.embeddings:
            logger.warning("No embeddings to save")
            return
        
        # Convert to structured format
        data = {
            'entities': list(self.embeddings.keys()),
            'vectors': np.array(list(self.embeddings.values()))
        }
        
        np.savez_compressed(output_path, **data)
        logger.info(f"Embeddings saved to {output_path}")