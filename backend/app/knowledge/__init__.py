"""Knowledge bridge — filesystem vault search for uCore."""
from .routes import register_routes
from .vault import (
    get_document,
    get_document_content,
    list_documents,
    list_workspaces,
    semantic_search,
)


def setup(app) -> None:
    """Run extension lifecycle setup."""
    pass


__all__ = [
    "get_document",
    "get_document_content",
    "list_documents",
    "list_workspaces",
    "register_routes",
    "semantic_search",
    "setup",
]
