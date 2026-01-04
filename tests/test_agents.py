"""
Tests for agents module.
"""
import unittest
from src.graph_store.in_memory_store import InMemoryGraphStore
from src.agents.diagnose_agent import DiagnoseAgent
from src.pipeline.schemas import RefinementIssue


class TestDiagnoseAgent(unittest.TestCase):
    """Test DiagnoseAgent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.graph_store = InMemoryGraphStore()
        
        # Create test nodes
        self.graph_store.upsert_node(['Paper'], {
            'id': 'P1',
            'title': 'Test Paper',
            'year': 2023
            # Missing venue
        })
        
        self.graph_store.upsert_node(['Author'], {
            'id': 'A1',
            'name': 'John Doe'
            # Missing affiliation
        })
    
    def test_diagnose_issues(self):
        """Test issue detection."""
        agent = DiagnoseAgent(self.graph_store)
        issues = agent.run()
        
        self.assertIsInstance(issues, list)
        # Should detect missing venue
        paper_issues = [i for i in issues if i.entity_type == 'Paper']
        self.assertGreater(len(paper_issues), 0)


if __name__ == '__main__':
    unittest.main()

