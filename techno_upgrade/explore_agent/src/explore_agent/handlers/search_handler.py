"""Search handler for explore agent actions."""

import os
from typing import Any, Dict

from ..dependencies import get_logger
from ..tool_abstractions import ContentSearcher


_logger = get_logger("phoenix.explore_agent.handlers.search")


class SearchHandler:
    """Handles content search operations with file-as-directory bug fix."""

    def __init__(self, api: Any):
        """Initialize search handler.

        Args:
            api: Agent API instance
        """
        if api is None:
            raise ValueError("Agent API instance is required")
        self._api = api
        self._content_searcher = ContentSearcher(api)

    def search_content(
        self,
        pattern: str,
        directory: str = ".",
        files: list = None,
        regex: bool = True,
        case_sensitive: bool = False,
    ) -> Dict[str, Any]:
        """Search content with file-as-directory bug fix.

        Handles the case where directory is actually a file path,
        treating it as a single-item file list instead.

        Args:
            pattern: Search pattern
            directory: Directory to search in
            files: List of specific files to search
            regex: Whether to use regex matching
            case_sensitive: Whether search is case-sensitive

        Returns:
            Dict with success/detail/data
        """
        # BUG FIX: If directory is a file, treat it as a single-item file list
        if os.path.isfile(directory):
            files = [directory]
            directory = "."

        return self._content_searcher.search(
            pattern=pattern,
            files=files,
            directory=directory,
            regex=regex,
            case_sensitive=case_sensitive,
        )
