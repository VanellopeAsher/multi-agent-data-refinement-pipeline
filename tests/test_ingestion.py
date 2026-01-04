"""
Tests for ingestion module.
"""
import unittest
from src.ingestion.schema_mapping import SchemaMapping
from src.graph_store.in_memory_store import InMemoryGraphStore


class TestSchemaMapping(unittest.TestCase):
    """Test schema mapping functionality."""
    
    def test_map_paper(self):
        """Test paper mapping."""
        openalex_paper = {
            'id': 'https://openalex.org/W12345',
            'title': 'Test Paper',
            'abstract': 'Test abstract',
            'publication_year': 2023,
            'primary_location': {
                'source': {
                    'display_name': 'NeurIPS'
                }
            },
            'doi': 'https://doi.org/10.1234/test',
            'cited_by_count': 10,
            'local_pdf_path': '/path/to/pdf.pdf'
        }
        
        paper_node = SchemaMapping.map_paper(openalex_paper)
        
        self.assertEqual(paper_node['id'], 'W12345')
        self.assertEqual(paper_node['title'], 'Test Paper')
        self.assertEqual(paper_node['year'], 2023)
        self.assertEqual(paper_node['venue'], 'NeurIPS')
        self.assertEqual(paper_node['citation_count'], 10)


class TestIngestion(unittest.TestCase):
    """Test paper ingestion."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.graph_store = InMemoryGraphStore()
    
    def test_ingest_paper(self):
        """Test ingesting a single paper."""
        from src.ingestion.ingest_papers import PaperIngester
        
        ingester = PaperIngester(self.graph_store)
        
        openalex_paper = {
            'id': 'https://openalex.org/W12345',
            'title': 'Test Paper',
            'abstract': 'Test abstract',
            'publication_year': 2023,
            'authorships': [
                {
                    'author': {
                        'id': 'https://openalex.org/A123',
                        'display_name': 'John Doe'
                    },
                    'institutions': [
                        {'display_name': 'Test University'}
                    ]
                }
            ],
            'concepts': [
                {
                    'id': 'https://openalex.org/C123',
                    'display_name': 'Machine Learning',
                    'level': 1
                }
            ],
            'referenced_works': []
        }
        
        stats = ingester.ingest_paper(openalex_paper)
        
        self.assertTrue(stats['paper'])
        self.assertGreater(stats['authors'], 0)
        self.assertGreater(stats['concepts'], 0)


if __name__ == '__main__':
    unittest.main()

