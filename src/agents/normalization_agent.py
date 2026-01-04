import json
from typing import List
from src.agents.base import BaseAgent
from src.pipeline.schemas import SearchResult, NormalizedUpdate
from src.graph_store.base_store import BaseGraphStore


class NormalizationAgent(BaseAgent):
    """Standardizes entity names and values."""
    
    def __init__(self, graph_store: BaseGraphStore):
        super().__init__(graph_store, 'normalizationagent')
    
    def normalize_author_name(self, name: str) -> str:
        # Basic normalization
        name = name.strip()
        # Remove extra spaces
        name = ' '.join(name.split())
        return name
    
    def normalize_dataset_name(self, name: str) -> str:
        # Common normalizations
        normalizations = {
            'Image Net': 'ImageNet',
            'ILSVRC2012': 'ImageNet',
            'CIFAR-10': 'CIFAR10',
            'CIFAR-100': 'CIFAR100',
        }
        
        name = name.strip()
        for variant, standard in normalizations.items():
            if variant.lower() in name.lower():
                return standard
        
        return name
    
    def normalize_venue(self, venue: str) -> str:
        """
        Normalize venue names.
        
        Args:
            venue: Venue name
            
        Returns:
            Normalized venue
        """
        venue = venue.strip()
        # Standard venue names
        venue_map = {
            'NeurIPS': 'NeurIPS',
            'NIPS': 'NeurIPS',
            'ICML': 'ICML',
            'ICLR': 'ICLR',
        }
        
        for variant, standard in venue_map.items():
            if variant.lower() in venue.lower():
                return standard
        
        return venue
    
    def run(self, search_results: List[SearchResult]) -> List[NormalizedUpdate]:
        """
        Standardize entities based on search results.
        
        Args:
            search_results: List of search results
            
        Returns:
            List of normalized updates
        """
        normalized_updates = []
        
        # Group search results by issue
        issues_map = {}
        for result in search_results:
            issue_id = result.issue_id
            if issue_id not in issues_map:
                issues_map[issue_id] = []
            issues_map[issue_id].append(result)
        
        # Process each issue
        for issue_id, results in issues_map.items():
            # Get entity from graph
            entity = self.graph_store.get_node(issue_id)
            if not entity:
                continue
            
            # Determine entity type from labels or properties
            entity_type = 'Paper'  # Default
            if 'Author' in str(entity.get('labels', [])):
                entity_type = 'Author'
            elif 'Concept' in str(entity.get('labels', [])):
                entity_type = 'Concept'
            elif 'Resource' in str(entity.get('labels', [])):
                entity_type = 'Resource'
            
            # Use LLM to extract normalized values from search results
            prompt = f"""
            Based on the following search results, extract and normalize the missing information:
            
            Entity: {json.dumps(entity, indent=2)[:500]}
            Search Results:
            {json.dumps([r.dict() for r in results], indent=2)[:2000]}
            
            Return a JSON object with normalized values for missing fields.
            For author names, use standard format (First Last).
            For venues, use standard abbreviations.
            For datasets/models, use canonical names.
            """
            
            try:
                llm_response = self.call_llm(prompt, temperature=0.3)
                # Parse LLM response
                # (Simplified - in production would parse JSON properly)
                
                # Create normalized updates based on search results
                for result in results:
                    if result.source == 'openalex':
                        # Extract from OpenAlex data
                        try:
                            openalex_data = json.loads(result.content)
                            if 'primary_location' in openalex_data:
                                venue = openalex_data['primary_location'].get('source', {}).get('display_name')
                                if venue:
                                    normalized_venue = self.normalize_venue(venue)
                                    normalized_updates.append(NormalizedUpdate(
                                        issue_id=issue_id,
                                        entity_type=entity_type,
                                        entity_id=issue_id,
                                        normalized_value=normalized_venue,
                                        original_value=entity.get('venue', ''),
                                        confidence=0.8,
                                        metadata={'field': 'venue'}
                                    ))
                        except:
                            pass
                    
                    elif result.source == 'pdf' and 'citation_context' in result.metadata.get('field', ''):
                        # Extract citation context
                        normalized_updates.append(NormalizedUpdate(
                            issue_id=issue_id,
                            entity_type='Edge',
                            entity_id=issue_id,
                            normalized_value=result.content[:500],
                            original_value='',
                            confidence=0.7,
                            metadata={'field': 'citation_context'}
                        ))
                    
                    elif result.source == 'web' and 'affiliation' in result.metadata.get('field', ''):
                        # Extract affiliation (simplified)
                        normalized_updates.append(NormalizedUpdate(
                            issue_id=issue_id,
                            entity_type='Author',
                            entity_id=issue_id,
                            normalized_value=result.content[:200],
                            original_value=entity.get('affiliation', ''),
                            confidence=0.5,
                            metadata={'field': 'affiliation'}
                        ))
            
            except Exception as e:
                print(f"Error in normalization: {e}")
        
        return normalized_updates

