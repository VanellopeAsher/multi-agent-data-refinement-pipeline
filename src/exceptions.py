class TavilyQuotaExceededError(Exception):
    """Raised when Tavily API quota is exceeded."""
    pass


class PipelineInterruptedError(Exception):
    """Raised when pipeline is interrupted and needs to resume from checkpoint."""
    pass

