"""Top-level pytest configuration for uCore repository.
Ensures required plugins are loaded before any subdirectory conftest files.
"""

import pytest

# Load pytest-asyncio globally
pytest_plugins = ["pytest_asyncio"]
