"""SnackMachine MCP Knowledge Conduit.

Exposes knowledge tools (search, ask, extract, summarize) over MCP
for LLMs to interact with vault documents, shared memory, and doclang parsing.

Built on:
- library_index: FTS5 indexed search across all 5 vault layers
- ai_bridge: AI-ranked search with agent-specific boosting
- doclang: Markdown/wiki-link/section parsing
- knowledge_layer: multi-agent shared memory pub/sub/query
- bridge: MCP query/status/chat HTTP routes
"""
from __future__ import annotations