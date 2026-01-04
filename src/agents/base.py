from abc import ABC, abstractmethod
from typing import Any, Optional
from src.utils import LLM
from src.llm_logger import LLMLogger
from src.config import MODEL_NAME, PLATFORM
from src.graph_store.base_store import BaseGraphStore


class BaseAgent(ABC):
    """Base class for all agents with LLM logging."""
    
    def __init__(self, graph_store: BaseGraphStore, agent_name: str):
        self.graph_store = graph_store
        self.agent_name = agent_name
        self.llm = LLM(model_name=MODEL_NAME, platform=PLATFORM)
        self.logger = LLMLogger(agent_name)
    
    def call_llm(
        self,
        prompt: str,
        temperature: float = 0.7,
        web_search: bool = False,
        metadata: Optional[dict] = None
    ) -> str:
        response = self.llm.generate(
            prompt=prompt,
            temperature=temperature,
            web_search=web_search
        )
        
        if self.llm.last_usage:
            self.logger.log_usage(
                prompt=prompt,
                response=response,
                input_tokens=self.llm.last_usage.prompt_tokens,
                output_tokens=self.llm.last_usage.completion_tokens,
                total_tokens=self.llm.last_usage.total_tokens,
                model_name=MODEL_NAME,
                platform=PLATFORM,
                metadata=metadata
            )
        
        return response
    
    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Must be implemented by subclasses."""
        pass

