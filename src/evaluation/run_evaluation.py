import json
import os
from typing import Dict, Any
from src.config import RAW_DATA_DIR, REFINED_DIR
from src.evaluation.metrics import GraphMetrics
from src.graph_store.neo4j_store import Neo4jGraphStore


class GraphEvaluator:
    """Evaluates refined graph against original OpenAlex data."""
    
    def __init__(self, graph_store: Neo4jGraphStore):
        self.graph_store = graph_store
        self.metrics = GraphMetrics(graph_store)
    
    def load_openalex_data(self, filename: str = 'papers.json') -> Dict[str, Any]:
        filepath = os.path.join(RAW_DATA_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def export_refined_graph(self, filename: str = 'refined_graph_round1.json'):
        filepath = os.path.join(REFINED_DIR, filename)
        self.graph_store.export_snapshot(filepath)
        print(f"Exported refined graph to {filepath}")
    
    def compare(self) -> Dict[str, Any]:
        openalex_data = self.load_openalex_data()
        openalex_papers = openalex_data.get('all_papers', [])
        
        refined_metrics = self.metrics.calculate_all()
        openalex_stats = {
            'total_papers': len(openalex_papers),
            'papers_with_abstract': sum(1 for p in openalex_papers if p.get('abstract')),
            'papers_with_venue': sum(1 for p in openalex_papers if p.get('primary_location', {}).get('source')),
                    'papers_with_concepts': sum(1 for p in openalex_papers if p.get('concepts')),
        }
        
        graph_stats_query = """
        MATCH (p:Paper)
        RETURN count(p) as papers,
               count(DISTINCT (p)-[:WRITTEN_BY]->()) as author_relationships,
               count(DISTINCT (p)-[:CENTERS_ON]->()) as concept_relationships,
               count(DISTINCT (p)-[:CITES]->()) as citation_relationships
        """
        graph_stats = self.graph_store.query(graph_stats_query)[0]
        
        comparison = {
            'openalex_baseline': openalex_stats,
            'refined_graph_stats': graph_stats,
            'refined_metrics': refined_metrics,
            'improvements': {
                'completeness': refined_metrics['completeness']['overall'],
                'context_coverage': refined_metrics['retrieval']['context_coverage']
            }
        }
        
        return comparison
    
    def run(self, export_graph: bool = True):
        print("Running evaluation...")
        
        if export_graph:
            self.export_refined_graph()
        
        comparison = self.compare()
        
        print("\n=== Evaluation Results ===")
        print(f"OpenAlex Papers: {comparison['openalex_baseline']['total_papers']}")
        print(f"Refined Graph Papers: {comparison['refined_graph_stats']['papers']}")
        print(f"\nCompleteness Score: {comparison['refined_metrics']['completeness']['overall']:.2%}")
        print(f"Context Coverage: {comparison['refined_metrics']['retrieval']['context_coverage']:.2%}")
        
        return comparison


if __name__ == "__main__":
    graph_store = Neo4jGraphStore()
    try:
        evaluator = GraphEvaluator(graph_store)
        evaluator.run()
    finally:
        graph_store.close()

