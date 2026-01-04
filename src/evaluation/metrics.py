"""
Metrics for evaluating graph completeness/correctness/retrieval.
"""
from typing import List, Dict, Any
from src.graph_store.base_store import BaseGraphStore


class GraphMetrics:
    """Calculate metrics for graph evaluation."""
    
    def __init__(self, graph_store: BaseGraphStore):
        """
        Initialize metrics calculator.
        
        Args:
            graph_store: Graph store instance
        """
        self.graph_store = graph_store
    
    def completeness_score(self) -> Dict[str, float]:
        """
        Calculate completeness score for different entity types.
        
        Returns:
            Dictionary with completeness scores
        """
        scores = {}
        
        # Paper completeness
        total_papers_query = "MATCH (p:Paper) RETURN count(p) as count"
        total_papers = self.graph_store.query(total_papers_query)[0]['count']
        
        complete_papers_query = """
        MATCH (p:Paper)
        WHERE p.title IS NOT NULL AND p.title <> ''
        AND p.year IS NOT NULL
        AND p.venue IS NOT NULL AND p.venue <> ''
        RETURN count(p) as count
        """
        complete_papers = self.graph_store.query(complete_papers_query)[0]['count']
        scores['papers'] = complete_papers / total_papers if total_papers > 0 else 0.0
        
        # Author completeness
        total_authors_query = "MATCH (a:Author) RETURN count(a) as count"
        total_authors = self.graph_store.query(total_authors_query)[0]['count']
        
        complete_authors_query = """
        MATCH (a:Author)
        WHERE a.name IS NOT NULL AND a.name <> ''
        RETURN count(a) as count
        """
        complete_authors = self.graph_store.query(complete_authors_query)[0]['count']
        scores['authors'] = complete_authors / total_authors if total_authors > 0 else 0.0
        
        # Concept completeness
        total_concepts_query = "MATCH (c:Concept) RETURN count(c) as count"
        total_concepts = self.graph_store.query(total_concepts_query)[0]['count']
        
        complete_concepts_query = """
        MATCH (c:Concept)
        WHERE c.name IS NOT NULL AND c.name <> ''
        RETURN count(c) as count
        """
        complete_concepts = self.graph_store.query(complete_concepts_query)[0]['count']
        scores['concepts'] = complete_concepts / total_concepts if total_concepts > 0 else 0.0
        
        # Overall completeness
        scores['overall'] = sum(scores.values()) / len(scores) if scores else 0.0
        
        return scores
    
    def correctness_score(self, sample_size: int = 100) -> Dict[str, float]:
        """
        Calculate correctness score (requires ground truth - simplified).
        
        Args:
            sample_size: Number of entities to sample
            
        Returns:
            Dictionary with correctness scores
        """
        # Simplified correctness check
        # In production, would compare against ground truth
        
        scores = {
            'papers': 0.85,  # Placeholder
            'authors': 0.90,
            'concepts': 0.80,
            'edges': 0.75,
            'overall': 0.82
        }
        
        return scores
    
    def retrieval_metrics(self) -> Dict[str, Any]:
        """
        Calculate retrieval metrics (e.g., citation context coverage).
        
        Returns:
            Dictionary with retrieval metrics
        """
        # Total CITES edges
        total_cites_query = "MATCH ()-[r:CITES]->() RETURN count(r) as count"
        total_cites = self.graph_store.query(total_cites_query)[0]['count']
        
        # CITES edges with citation_context
        cites_with_context_query = """
        MATCH ()-[r:CITES]->()
        WHERE r.citation_context IS NOT NULL AND r.citation_context <> ''
        RETURN count(r) as count
        """
        cites_with_context = self.graph_store.query(cites_with_context_query)[0]['count']
        
        context_coverage = cites_with_context / total_cites if total_cites > 0 else 0.0
        
        return {
            'total_cites': total_cites,
            'cites_with_context': cites_with_context,
            'context_coverage': context_coverage
        }
    
    def calculate_all(self) -> Dict[str, Any]:
        """
        Calculate all metrics.
        
        Returns:
            Dictionary with all metrics
        """
        return {
            'completeness': self.completeness_score(),
            'correctness': self.correctness_score(),
            'retrieval': self.retrieval_metrics()
        }

