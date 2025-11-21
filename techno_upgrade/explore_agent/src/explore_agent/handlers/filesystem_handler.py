"""Filesystem handler for explore agent actions."""

import os
from typing import Any, Dict

from ..dependencies import get_logger
from ..tool_abstractions import FileFinder


_logger = get_logger("phoenix.explore_agent.handlers.filesystem")


class FilesystemHandler:
    """Handles filesystem operations (list and read) with API validation."""

    def __init__(self, api: Any):
        """Initialize filesystem handler.

        Args:
            api: Agent API instance
        """
        if api is None:
            raise ValueError("Agent API instance is required")
        self._api = api
        self._file_finder = FileFinder(api)

    def list(self, path: str = ".") -> Dict[str, Any]:
        """List directory contents with API validation.

        Args:
            path: Directory path to list

        Returns:
            Dict with success/detail/data
        """
        fs_api = getattr(self._api, "filesystem", None)
        if fs_api is None:
            return {
                "success": False,
                "detail": "Filesystem API is unavailable",
                "error": "api_unavailable",
            }

        try:
            listing = fs_api.list_directory(path)
            return {
                "success": True,
                "detail": f"Listed {path}",
                "data": listing,
                "type": "filesystem.list_directory",
            }
        except FileNotFoundError:
            _logger.info("Filesystem target not found", verb="list", target=path)
            return {
                "success": False,
                "detail": f"Filesystem target not found: {path}",
                "error": "file_not_found",
            }
        except OSError as exc:
            _logger.warning(
                "Filesystem operation failed", verb="list", target=path, error=str(exc)
            )
            return {
                "success": False,
                "detail": f"Filesystem error for {path}: {exc}",
                "error": "filesystem_error",
            }

    def read(self, path: str) -> Dict[str, Any]:
        """Read file contents with directory detection.

        Automatically lists directory if path points to a directory.

        Args:
            path: File path to read

        Returns:
            Dict with success/detail/data
        """
        fs_api = getattr(self._api, "filesystem", None)
        if fs_api is None:
            return {
                "success": False,
                "detail": "Filesystem API is unavailable",
                "error": "api_unavailable",
            }

        if not path:
            return {
                "success": False,
                "detail": "Path is required for read operation",
                "error": "missing_argument",
            }

        try:
            # Check if it's a directory - if so, list it instead
            if os.path.isdir(path):
                _logger.info("Cannot read directory, using list instead", target=path)
                return self.list(path)

            content = fs_api.read(path)
            return {
                "success": True,
                "detail": f"Read {path}",
                "data": content,
                "type": "filesystem.read",
            }
        except FileNotFoundError:
            _logger.info("Filesystem target not found", verb="read", target=path)
            return {
                "success": False,
                "detail": f"Filesystem target not found: {path}",
                "error": "file_not_found",
            }
        except OSError as exc:
            _logger.warning(
                "Filesystem operation failed", verb="read", target=path, error=str(exc)
            )
            return {
                "success": False,
                "detail": f"Filesystem error for {path}: {exc}",
                "error": "filesystem_error",
            }
