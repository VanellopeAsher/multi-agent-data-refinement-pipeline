import os
import json
from typing import List
from src.agents.base import BaseAgent
from src.pipeline.schemas import RefinementIssue, SearchResult
from src.graph_store.base_store import BaseGraphStore
from src.utils import LLM
from src.config import MODEL_NAME, PLATFORM
from src.exceptions import TavilyQuotaExceededError


class SearchAgent(BaseAgent):
    """Retrieves supporting evidence from web, OpenAlex, and PDFs."""
    
    def __init__(self, graph_store: BaseGraphStore):
        super().__init__(graph_store, 'searchagent')
        self.web_llm = LLM(model_name=MODEL_NAME, platform=PLATFORM)
    
    def search_web(self, query: str) -> List[str]:
        """Search web using Tavily API. Raises TavilyQuotaExceededError if quota exceeded."""
        try:
            return self.web_llm._search_web(query)
        except TavilyQuotaExceededError:
            raise
        except Exception as e:
            print(f"Error in web search: {e}")
            return []
    
    def search_openalex(self, paper_id: str) -> dict:
        import requests
        
        url = f"https://api.openalex.org/works/{paper_id}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error querying OpenAlex: {e}")
            return {}
    
    def extract_from_pdf(self, pdf_path: str, query: str) -> str:
        if not pdf_path or not os.path.exists(pdf_path):
            return ""
        
        try:
            import PyPDF2
            
            # Extract text from PDF
            text_content = ""
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages[:10]:  # Limit to first 10 pages
                    text_content += page.extract_text() + "\n"
            
            # Use LLM to extract relevant information
            prompt = f"""
            Extract the following information from this paper:
            {query}
            
            Paper text (first 10 pages):
            {text_content[:5000]}  # Limit text length
            
            Return the extracted information in a structured format.
            """
            
            response = self.call_llm(prompt, temperature=0.3)
            return response
            
        except Exception as e:
            print(f"Error extracting from PDF: {e}")
            return ""
    
    def run(self, issues: List[RefinementIssue]) -> List[SearchResult]:
        """Retrieve evidence for detected issues. Raises TavilyQuotaExceededError if quota exceeded."""
        search_results = []
        
        for issue in issues:
            # Get entity from graph
            entity = self.graph_store.get_node(issue.entity_id)
            if not entity:
                continue
            
            # Search based on issue type
            if issue.issue_type == 'missing_field':
                if issue.entity_type == 'Paper':
                    paper_title = entity.get('title', '')
                    missing_fields = issue.metadata.get('missing_fields', [])
                    
                    # Web search for missing information
                    if 'venue' in missing_fields:
                        query = f"{paper_title} conference venue"
                        try:
                            urls = self.search_web(query)
                            search_results.append(SearchResult(
                                issue_id=issue.entity_id,
                                source='web',
                                content=f"Found URLs: {', '.join(urls[:3])}",
                                confidence=0.6,
                                metadata={'urls': urls, 'field': 'venue'}
                            ))
                        except TavilyQuotaExceededError:
                            # Re-raise immediately to stop pipeline
                            raise
                    
                    # OpenAlex re-query
                    openalex_data = self.search_openalex(issue.entity_id)
                    if openalex_data:
                        search_results.append(SearchResult(
                            issue_id=issue.entity_id,
                            source='openalex',
                            content=json.dumps(openalex_data, indent=2)[:1000],
                            confidence=0.8,
                            metadata={'field': 'metadata'}
                        ))
                    
                    # PDF extraction
                    pdf_path = entity.get('local_pdf_path')
                    if pdf_path:
                        extracted = self.extract_from_pdf(
                            pdf_path,
                            f"Extract: {', '.join(missing_fields)}"
                        )
                        if extracted:
                            search_results.append(SearchResult(
                                issue_id=issue.entity_id,
                                source='pdf',
                                content=extracted,
                                confidence=0.7,
                                metadata={'field': 'pdf_extraction'}
                            ))
            
            elif issue.issue_type == 'missing_relationship':
                if 'CITES' in issue.description:
                    # Extract citation context from PDF
                    src_id = issue.metadata.get('src_id')
                    dst_id = issue.metadata.get('dst_id')
                    
                    if src_id:
                        src_paper = self.graph_store.get_node(src_id)
                        if src_paper:
                            pdf_path = src_paper.get('local_pdf_path')
                            if pdf_path:
                                extracted = self.extract_from_pdf(
                                    pdf_path,
                                    f"Find citation context for paper {dst_id}"
                                )
                                if extracted:
                                    search_results.append(SearchResult(
                                        issue_id=issue.entity_id,
                                        source='pdf',
                                        content=extracted,
                                        confidence=0.7,
                                        metadata={'field': 'citation_context'}
                                    ))
            
            elif issue.issue_type == 'missing_field' and issue.entity_type == 'Author':
                # Search for author affiliation
                author_name = entity.get('name', '')
                if author_name:
                    query = f"{author_name} affiliation"
                    try:
                        urls = self.search_web(query)
                        search_results.append(SearchResult(
                            issue_id=issue.entity_id,
                            source='web',
                            content=f"Found URLs: {', '.join(urls[:3])}",
                            confidence=0.5,
                            metadata={'urls': urls, 'field': 'affiliation'}
                        ))
                    except TavilyQuotaExceededError:
                        # Re-raise immediately to stop pipeline
                        raise
        
        return search_results

