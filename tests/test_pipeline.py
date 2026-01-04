"""
Tests for pipeline module.
"""
import unittest
from src.graph_store.in_memory_store import InMemoryGraphStore
from src.pipeline.orchestrator import MultiAgentRefinementPipeline


class TestPipeline(unittest.TestCase):
    """Test refinement pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.graph_store = InMemoryGraphStore()
        
        # Create test graph
        self.graph_store.upsert_node(['Paper'], {
            'id': 'P1',
            'title': 'Test Paper',
            'year': 2023
        })
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        pipeline = MultiAgentRefinementPipeline(self.graph_store, round_number=1)
        self.assertIsNotNone(pipeline.diagnose_agent)
        self.assertIsNotNone(pipeline.search_agent)
        self.assertIsNotNone(pipeline.normalization_agent)
        self.assertIsNotNone(pipeline.coding_agent)
        self.assertIsNotNone(pipeline.review_agent)


if __name__ == '__main__':
    unittest.main()

