"""uCore connection adapters; uFlow retains authority over task Markdown.

Lifecycle: existing maintenance scheduler; storage: settings.data_dir/connections.sqlite3.
No separate daemon. Disable a connection to stop polling; disconnect removes its token.
Canonical records survive disconnect. Source copies never silently overwrite conflicts.
"""
