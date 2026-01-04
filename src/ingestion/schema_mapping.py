"""
Define canonical graph schema and mapping rules from OpenAlex to target schema.
"""
from typing import List, Dict, Any, Optional


class SchemaMapping:
    """
    Maps OpenAlex metadata to canonical graph schema.
    
    Nodes:
    - Paper(id, title, abstract, year, venue, doi, citation_count, local_pdf_path)
    - Author(id, name, affiliation)
    - Concept(id, name, level, field)
    - Resource(id, name, resource_type, url)
    
    Edges:
    - CITES
    - WRITTEN_BY
    - CENTERS_ON
    - USES
    """
    
    @staticmethod
    def map_paper(openalex_paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map OpenAlex paper to Paper node.
        
        Args:
            openalex_paper: OpenAlex paper dictionary
            
        Returns:
            Paper node dictionary
        """
        # Extract OpenAlex ID
        paper_id = openalex_paper.get('id', '').replace('https://openalex.org/', '')
        
        # Extract venue
        venue = None
        primary_location = openalex_paper.get('primary_location', {})
        if primary_location:
            source = primary_location.get('source', {})
            if source:
                venue = source.get('display_name')
        
        # Extract DOI
        doi = None
        doi_url = openalex_paper.get('doi', '')
        if doi_url:
            doi = doi_url.replace('https://doi.org/', '')
        
        return {
            'id': paper_id,
            'title': openalex_paper.get('title', ''),
            'abstract': openalex_paper.get('abstract', ''),
            'year': openalex_paper.get('publication_year'),
            'venue': venue,
            'doi': doi,
            'citation_count': openalex_paper.get('cited_by_count', 0),
            'local_pdf_path': openalex_paper.get('local_pdf_path')
        }
    
    @staticmethod
    def map_authors(openalex_paper: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Map OpenAlex authorships to Author nodes.
        
        Args:
            openalex_paper: OpenAlex paper dictionary
            
        Returns:
            List of Author node dictionaries
        """
        authors = []
        authorships = openalex_paper.get('authorships', [])
        
        for authorship in authorships:
            author = authorship.get('author', {})
            if not author:
                continue
            
            author_id = author.get('id', '').replace('https://openalex.org/', '')
            author_name = author.get('display_name', '')
            
            # Extract affiliation
            affiliation = None
            institutions = authorship.get('institutions', [])
            if institutions:
                affiliation = institutions[0].get('display_name')
            
            authors.append({
                'id': author_id,
                'name': author_name,
                'affiliation': affiliation
            })
        
        return authors
    
    @staticmethod
    def map_concepts(openalex_paper: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Map OpenAlex concepts to Concept nodes.
        
        Args:
            openalex_paper: OpenAlex paper dictionary
            
        Returns:
            List of Concept node dictionaries
        """
        concepts = []
        openalex_concepts = openalex_paper.get('concepts', [])
        
        for concept in openalex_concepts:
            concept_id = concept.get('id', '').replace('https://openalex.org/', '')
            concept_name = concept.get('display_name', '')
            level = concept.get('level', 0)
            field = None  # OpenAlex doesn't directly provide field, could derive from domain
            
            concepts.append({
                'id': concept_id,
                'name': concept_name,
                'level': level,
                'field': field
            })
        
        return concepts
    
    @staticmethod
    def map_resources(openalex_paper: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Map OpenAlex resources to Resource nodes.
        
        Note: OpenAlex doesn't directly map to resources (datasets/models/tools).
        This will be populated during refinement stage.
        
        Args:
            openalex_paper: OpenAlex paper dictionary
            
        Returns:
            List of Resource node dictionaries (empty for initial mapping)
        """
        # Resources are typically extracted from PDFs during refinement
        return []
    
    @staticmethod
    def map_citations(openalex_paper: Dict[str, Any]) -> List[str]:
        """
        Extract referenced work IDs for CITES edges.
        
        Args:
            openalex_paper: OpenAlex paper dictionary
            
        Returns:
            List of referenced work IDs
        """
        referenced_works = openalex_paper.get('referenced_works', [])
        return [
            ref.replace('https://openalex.org/', '')
            for ref in referenced_works
        ]
    
    @staticmethod
    def map_to_graph_structure(openalex_paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a single OpenAlex paper to complete graph structure.
        
        Args:
            openalex_paper: OpenAlex paper dictionary
            
        Returns:
            Dictionary containing nodes and edges
        """
        paper_node = SchemaMapping.map_paper(openalex_paper)
        author_nodes = SchemaMapping.map_authors(openalex_paper)
        concept_nodes = SchemaMapping.map_concepts(openalex_paper)
        resource_nodes = SchemaMapping.map_resources(openalex_paper)
        cited_paper_ids = SchemaMapping.map_citations(openalex_paper)
        
        return {
            'paper': paper_node,
            'authors': author_nodes,
            'concepts': concept_nodes,
            'resources': resource_nodes,
            'cited_paper_ids': cited_paper_ids
        }

