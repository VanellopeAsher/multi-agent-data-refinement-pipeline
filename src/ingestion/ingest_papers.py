"""
Read papers.json, apply mapping rules, and write nodes/edges to Neo4j.
"""
import json
import os
from typing import List, Dict, Any
from src.config import RAW_DATA_DIR
from src.ingestion.schema_mapping import SchemaMapping
from src.graph_store.neo4j_store import Neo4jGraphStore


class PaperIngester:
    """Ingests papers into Neo4j graph."""
    
    def __init__(self, graph_store: Neo4jGraphStore = None):
        """
        Initialize ingester.
        
        Args:
            graph_store: Graph store instance (creates new if None)
        """
        self.graph_store = graph_store or Neo4jGraphStore()
    
    def load_papers(self, filename: str = 'papers.json') -> Dict[str, Any]:
        """
        Load papers from JSON file.
        
        Args:
            filename: Input JSON filename
            
        Returns:
            Papers data dictionary
        """
        filepath = os.path.join(RAW_DATA_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def ingest_paper(self, openalex_paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingest a single paper into the graph.
        
        Args:
            openalex_paper: OpenAlex paper dictionary
            
        Returns:
            Dictionary with ingestion statistics
        """
        stats = {
            'paper': False,
            'authors': 0,
            'concepts': 0,
            'resources': 0,
            'edges': 0
        }
        
        # Map to graph structure
        graph_data = SchemaMapping.map_to_graph_structure(openalex_paper)
        
        # Create Paper node
        paper_node = graph_data['paper']
        paper_id = self.graph_store.upsert_node(['Paper'], paper_node)
        stats['paper'] = True
        
        # Create Author nodes and WRITTEN_BY edges
        for author in graph_data['authors']:
            author_id = self.graph_store.upsert_node(['Author'], author)
            self.graph_store.add_edge(paper_id, 'WRITTEN_BY', author_id)
            stats['authors'] += 1
            stats['edges'] += 1
        
        # Create Concept nodes and CENTERS_ON edges
        for concept in graph_data['concepts']:
            concept_id = self.graph_store.upsert_node(['Concept'], concept)
            self.graph_store.add_edge(paper_id, 'CENTERS_ON', concept_id)
            stats['concepts'] += 1
            stats['edges'] += 1
        
        # Create Resource nodes and USES edges
        for resource in graph_data['resources']:
            resource_id = self.graph_store.upsert_node(['Resource'], resource)
            self.graph_store.add_edge(paper_id, 'USES', resource_id)
            stats['resources'] += 1
            stats['edges'] += 1
        
        # Create CITES edges (note: cited papers may not exist yet)
        for cited_id in graph_data['cited_paper_ids']:
            # Try to create edge - cited paper may be added later
            self.graph_store.add_edge(paper_id, 'CITES', cited_id)
            stats['edges'] += 1
        
        return stats
    
    def ingest_all(self, filename: str = 'papers.json') -> Dict[str, Any]:
        """
        Ingest all papers from JSON file.
        
        Args:
            filename: Input JSON filename
            
        Returns:
            Summary statistics
        """
        data = self.load_papers(filename)
        all_papers = data.get('all_papers', [])
        
        print(f"Ingesting {len(all_papers)} papers...")
        
        total_stats = {
            'papers': 0,
            'authors': 0,
            'concepts': 0,
            'resources': 0,
            'edges': 0
        }
        
        for i, paper in enumerate(all_papers):
            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(all_papers)} papers...")
            
            stats = self.ingest_paper(paper)
            total_stats['papers'] += 1 if stats['paper'] else 0
            total_stats['authors'] += stats['authors']
            total_stats['concepts'] += stats['concepts']
            total_stats['resources'] += stats['resources']
            total_stats['edges'] += stats['edges']
        
        print(f"\nIngestion complete!")
        print(f"  Papers: {total_stats['papers']}")
        print(f"  Authors: {total_stats['authors']}")
        print(f"  Concepts: {total_stats['concepts']}")
        print(f"  Resources: {total_stats['resources']}")
        print(f"  Edges: {total_stats['edges']}")
        
        return total_stats
    
    def close(self):
        """Close graph store connection."""
        if self.graph_store:
            self.graph_store.close()


if __name__ == "__main__":
    ingester = PaperIngester()
    try:
        ingester.ingest_all()
    finally:
        ingester.close()

