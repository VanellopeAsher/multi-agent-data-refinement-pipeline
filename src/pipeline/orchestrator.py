import os
import json
from typing import List, Dict, Any, Optional
from src.pipeline.schemas import (
    RefinementIssue, SearchResult, NormalizedUpdate,
    GraphUpdate, ReviewedGraphUpdate
)
from src.graph_store.base_store import BaseGraphStore
from src.agents.diagnose_agent import DiagnoseAgent
from src.agents.search_agent import SearchAgent
from src.agents.normalization_agent import NormalizationAgent
from src.agents.coding_agent import CodingAgent
from src.agents.review_agent import ReviewAgent
from src.exceptions import TavilyQuotaExceededError
from src.config import CHECKPOINT_DIR


class MultiAgentRefinementPipeline:
    """Orchestrates the multi-agent refinement pipeline."""
    
    def __init__(self, graph_store: BaseGraphStore, round_number: int = 1):
        self.graph_store = graph_store
        self.round_number = round_number
        self.checkpoint_file = os.path.join(CHECKPOINT_DIR, f"checkpoint_round{round_number}.json")
        
        self.diagnose_agent = DiagnoseAgent(graph_store)
        self.search_agent = SearchAgent(graph_store)
        self.normalization_agent = NormalizationAgent(graph_store)
        self.coding_agent = CodingAgent(graph_store)
        self.review_agent = ReviewAgent(graph_store)
    
    def _save_checkpoint(self, step: str, results: Dict[str, Any]):
        checkpoint = {
            'round': self.round_number,
            'step': step,
            'results': results,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)
    
    def _load_checkpoint(self) -> Optional[Dict[str, Any]]:
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def _clear_checkpoint(self):
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
    
    def run(self, resume: bool = True) -> Dict[str, Any]:
        """Run the complete refinement pipeline. Raises TavilyQuotaExceededError if quota exceeded."""
        checkpoint = None
        if resume:
            checkpoint = self._load_checkpoint()
            if checkpoint:
                print(f"\n⚠️  Found checkpoint from step: {checkpoint['step']}")
                print(f"   Timestamp: {checkpoint.get('timestamp', 'unknown')}")
                print("   Resuming from checkpoint...\n")
                results = checkpoint['results']
                start_step = checkpoint['step']
            else:
                results = {
                    'round': self.round_number,
                    'issues': [],
                    'search_results': [],
                    'normalized_updates': [],
                    'tentative_update': None,
                    'final_update': None,
                    'statistics': {}
                }
                start_step = 'diagnose'
        else:
            results = {
                'round': self.round_number,
                'issues': [],
                'search_results': [],
                'normalized_updates': [],
                'tentative_update': None,
                'final_update': None,
                'statistics': {}
            }
            start_step = 'diagnose'
        
        print(f"Starting refinement pipeline round {self.round_number}...")
        
        try:
            if start_step == 'diagnose':
                print("\n[Step 1] DiagnoseAgent: Detecting issues...")
                issues: List[RefinementIssue] = self.diagnose_agent.run()
                results['issues'] = [issue.dict() for issue in issues]
                print(f"  Found {len(issues)} issues")
                self._save_checkpoint('search', results)
            
            if start_step in ['diagnose', 'search']:
                print("\n[Step 2] SearchAgent: Retrieving evidence...")
                if results['issues'] and isinstance(results['issues'][0], dict):
                    issues = [RefinementIssue(**issue) for issue in results['issues']]
                elif results['issues']:
                    issues = results['issues']
                else:
                    issues = []
                
                try:
                    search_results: List[SearchResult] = self.search_agent.run(issues)
                    results['search_results'] = [result.dict() for result in search_results]
                    print(f"  Retrieved {len(search_results)} search results")
                    self._save_checkpoint('normalize', results)
                except TavilyQuotaExceededError as e:
                    # Save checkpoint before stopping
                    self._save_checkpoint('search', results)
                    print("\n" + "=" * 60)
                    print("⚠️  WARNING: Tavily API Quota Exceeded!")
                    print("=" * 60)
                    print(f"\nError: {e}")
                    print("\nPipeline stopped and checkpoint saved.")
                    print(f"Checkpoint file: {self.checkpoint_file}")
                    print("\nTo resume after adding Tavily credits:")
                    print(f"  python -m src.scripts.run_refinement_pipeline --round {self.round_number} --resume")
                    print("=" * 60)
                    raise
            
            if start_step in ['diagnose', 'search', 'normalize']:
                print("\n[Step 3] NormalizationAgent: Standardizing entities...")
                if results['search_results'] and isinstance(results['search_results'][0], dict):
                    search_results = [SearchResult(**result) for result in results['search_results']]
                elif results['search_results']:
                    search_results = results['search_results']
                else:
                    search_results = []
                
                normalized_updates: List[NormalizedUpdate] = self.normalization_agent.run(search_results)
                results['normalized_updates'] = [update.dict() for update in normalized_updates]
                print(f"  Generated {len(normalized_updates)} normalized updates")
                self._save_checkpoint('code', results)
            
            if start_step in ['diagnose', 'search', 'normalize', 'code']:
                print("\n[Step 4] CodingAgent: Converting to graph updates...")
                if results['normalized_updates'] and isinstance(results['normalized_updates'][0], dict):
                    normalized_updates = [NormalizedUpdate(**update) for update in results['normalized_updates']]
                elif results['normalized_updates']:
                    normalized_updates = results['normalized_updates']
                else:
                    normalized_updates = []
                
                tentative_update: GraphUpdate = self.coding_agent.run(normalized_updates)
                results['tentative_update'] = tentative_update.dict()
                print(f"  Generated {len(tentative_update.node_updates)} node updates and {len(tentative_update.edge_updates)} edge updates")
                self._save_checkpoint('review', results)
            
            if start_step in ['diagnose', 'search', 'normalize', 'code', 'review']:
                print("\n[Step 5] ReviewAgent: Validating updates...")
                if results['tentative_update'] and isinstance(results['tentative_update'], dict):
                    tentative_update = GraphUpdate(**results['tentative_update'])
                elif results['tentative_update']:
                    tentative_update = results['tentative_update']
                else:
                    tentative_update = GraphUpdate()
                
                final_update: ReviewedGraphUpdate = self.review_agent.run(tentative_update)
                results['final_update'] = final_update.dict()
                print(f"  Approved {len(final_update.node_updates)} node updates and {len(final_update.edge_updates)} edge updates")
                print(f"  Rejected {len(final_update.rejected_updates)} updates")
                print(f"  Pending human review: {len(final_update.pending_human)}")
                self._save_checkpoint('apply', results)
            
            print("\n[Step 6] Applying updates to graph...")
            if results['final_update'] and isinstance(results['final_update'], dict):
                final_update = ReviewedGraphUpdate(**results['final_update'])
                elif results['final_update']:
                    final_update = results['final_update']
                else:
                    final_update = ReviewedGraphUpdate()
            
            self._apply_updates(final_update)
            
            results['statistics'] = {
                'issues_detected': len(results['issues']),
                'search_results': len(results['search_results']),
                'normalized_updates': len(results['normalized_updates']),
                'node_updates_applied': len(final_update.node_updates),
                'edge_updates_applied': len(final_update.edge_updates),
                'updates_rejected': len(final_update.rejected_updates),
                'pending_human': len(final_update.pending_human)
            }
            
            self._clear_checkpoint()
            
            print("\nPipeline complete!")
            return results
            
        except TavilyQuotaExceededError:
            raise
        except Exception as e:
            print(f"\n⚠️  Error occurred: {e}")
            print("Saving checkpoint...")
            self._save_checkpoint(start_step, results)
            raise
    
    def _apply_updates(self, update: ReviewedGraphUpdate):
        # Apply node updates
        for node_update in update.node_updates:
            if node_update.operation == 'create' or node_update.operation == 'update':
                self.graph_store.upsert_node([node_update.node_type], {
                    'id': node_update.node_id,
                    **node_update.fields
                })
            elif node_update.operation == 'merge' and node_update.merge_with:
                # Merge nodes (implementation depends on graph store)
                # This is a simplified version
                src_node = self.graph_store.get_node(node_update.node_id)
                dst_node = self.graph_store.get_node(node_update.merge_with)
                if src_node and dst_node:
                    # Merge properties
                    merged_fields = {**dst_node, **node_update.fields}
                    self.graph_store.upsert_node([node_update.node_type], {
                        'id': node_update.merge_with,
                        **merged_fields
                    })
                    # Delete source node (simplified - should also migrate edges)
                    # In production, this would be more complex
            elif node_update.operation == 'delete':
                self.graph_store.delete_node(node_update.node_id)
        
        # Apply edge updates
        for edge_update in update.edge_updates:
            if edge_update.operation == 'create' or edge_update.operation == 'update':
                self.graph_store.add_edge(
                    edge_update.src_id,
                    edge_update.rel_type,
                    edge_update.dst_id,
                    edge_update.properties
                )
            elif edge_update.operation == 'delete':
                self.graph_store.delete_edge(
                    edge_update.src_id,
                    edge_update.rel_type,
                    edge_update.dst_id
                )

