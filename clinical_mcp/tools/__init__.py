"""
MCP tool registry.
"""
from .document import DOCUMENT_TOOLS
from .search import SEARCH_TOOLS
from .analysis import ANALYSIS_TOOLS
from .validation import VALIDATION_TOOLS

TOOL_DEFINITIONS = (
    DOCUMENT_TOOLS +
    SEARCH_TOOLS +
    ANALYSIS_TOOLS +
    VALIDATION_TOOLS
)

__all__ = ["TOOL_DEFINITIONS"]
