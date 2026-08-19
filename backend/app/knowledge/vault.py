"""Compatibility imports for the uKnowledge-owned filesystem library.

Knowledge storage and search live in the separate uKnowledge package. Keeping
these names here avoids breaking existing uCore chat, MCP, and skill callers
while preventing a second implementation from drifting.
"""

from uknowledge.library import (
    get_document,
    get_document_content,
    list_documents,
    list_workspaces,
    search,
)

semantic_search = search

__all__ = [
    "get_document",
    "get_document_content",
    "list_documents",
    "list_workspaces",
    "semantic_search",
]
