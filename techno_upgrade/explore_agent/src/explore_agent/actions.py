"""Action execution for explore agent with Tool-Calling support."""

import json
from typing import Any, Callable, Dict, Tuple

from .dependencies import ConstitutionalViolationError, get_logger
from .handlers import (
    AnalysisHandler,
    FilesystemHandler,
    SearchHandler,
    ShellHandler,
)
from .tool_abstractions import (
    DirectoryAnalyzer,
    FileFinder,
)


_logger = get_logger("phoenix.explore_agent.actions")


class CommandParser:
    """Parses modern command string formats into (tool_name, args) tuples.

    Supports marker-based formats only:
    - Composite markers: "composite:analyze_directory:dir=.:pattern=*.py"
    - Semantic markers: "semantic:find_files:dir=.:pattern=*.py"
    """

    def parse(self, step: str) -> Tuple[str, Dict[str, Any]]:
        """Parse a command string and return (tool_name, arguments).

        Args:
            step: Command string in marker-based format

        Returns:
            Tuple of (tool_name, args_dict)

        Raises:
            ValueError: If the command format is invalid
        """
        if step.startswith("composite:"):
            return self._parse_marker(step, "composite")

        if step.startswith("semantic:"):
            return self._parse_marker(step, "semantic")

        raise ValueError(
            f"Invalid command format: {step}. "
            "Commands must use 'semantic:' or 'composite:' markers."
        )

    def _parse_marker(self, marker: str, prefix: str) -> Tuple[str, Dict[str, Any]]:
        """Parse composite or semantic marker format.

        Format: "prefix:tool_type:key1=value1:key2=value2"
        """
        parts = marker.split(":")
        if len(parts) < 2:
            raise ValueError(f"Invalid {prefix} marker: {marker}")

        tool_type = parts[1]

        # Parse key=value pairs
        params = {}
        for part in parts[2:]:
            if "=" in part:
                key, value = part.split("=", 1)
                params[key] = value

        # Map marker tool names to registry tool names
        tool_name_map = {
            # Composite tools
            "analyze_directory": "analyze_directory",
            "search_codebase": "search_codebase",
            # Semantic tools
            "find_files": "find_files_by_pattern",
            "find_files_by_pattern": "find_files_by_pattern",  # Direct mapping for Mistral
            "search_content": "search_content",
            "analyze_python": "analyze_python_file",
            "analyze_python_file": "analyze_python_file",  # Direct mapping for Mistral
            "filesystem_list": "filesystem_list",
            "filesystem_read": "filesystem_read",
            "shell_run": "shell_run",
        }

        tool_name = tool_name_map.get(tool_type)
        if not tool_name:
            raise ValueError(f"Unknown {prefix} tool: {tool_type}")

        # Normalize parameter names to match tool signatures
        args = self._normalize_marker_params(tool_name, params)

        return tool_name, args

    def _normalize_marker_params(
        self, tool_name: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Normalize marker parameters to match tool method signatures."""
        args = {}

        # Common parameter mappings
        if "dir" in params:
            args["directory"] = params["dir"]
        if "pattern" in params:
            # For find_files, it's name_pattern; for others, it's pattern
            if tool_name == "find_files_by_pattern":
                args["name_pattern"] = params["pattern"]
            else:
                args["pattern"] = params["pattern"]
        if "type" in params:
            args["file_type"] = params["type"]
        if "file" in params:
            args["file_path"] = params["file"]
        if "content" in params:
            args["content_pattern"] = params["content"]
        if "path" in params:
            args["path"] = params["path"]
        if "command" in params:
            args["command"] = params["command"]

        # Tool-specific parameters
        if tool_name == "search_content":
            args["regex"] = params.get("regex", "true").lower() == "true"
            args["case_sensitive"] = params.get("cs", "false").lower() == "true"
        elif tool_name == "analyze_python_file":
            # Mistral sends file_path directly
            if "file_path" in params:
                args["file_path"] = params["file_path"]
            args["analysis_type"] = params.get(
                "analysis_type", params.get("type", "all")
            )

        return args


class ActionExecutor:
    """Executes tool-calls from the LLM using semantic tool abstractions.

    This class follows the Registry Pattern:
    - Tool abstractions handle the business logic
    - Registry maps tool names to handlers
    - Parser handles multiple command formats
    - Executor orchestrates dispatch and error handling
    """

    def __init__(self, api: Any):
        if api is None:
            raise ValueError("Agent API instance is required")
        self._api = api
        self._parser = CommandParser()

        # Initialize semantic tool abstractions that are directly used
        self._file_finder = FileFinder(api)
        self._directory_analyzer = DirectoryAnalyzer(api)

        # Initialize dedicated handlers
        self._filesystem_handler = FilesystemHandler(api)
        self._search_handler = SearchHandler(api)
        self._analysis_handler = AnalysisHandler(api)
        self._shell_handler = ShellHandler(api)

        # Registry: Map tool names directly to handler methods
        self._tool_registry: Dict[str, Callable] = {
            # Composite tools (prevent context explosion)
            "analyze_directory": self._directory_analyzer.analyze,
            "search_codebase": self._directory_analyzer.search_codebase,
            # Semantic tools (high-level intelligence)
            "find_files_by_pattern": self._file_finder.search,
            "search_content": self._search_handler.search_content,
            "analyze_python_file": self._analysis_handler.analyze_python,
            # Legacy tools (for compatibility)
            "filesystem_list": self._filesystem_handler.list,
            "filesystem_read": self._filesystem_handler.read,
            "shell_run": self._shell_handler.run,
        }

    def execute_tool_call(self, tool_call: Any) -> Dict[str, Any]:
        """Execute a single tool-call object from the LLM.

        Args:
            tool_call: Object with .function.name and .function.arguments
                       (Mistral's ToolCall structure)

        Returns:
            Dict with success/detail/data
        """
        try:
            func_name = tool_call.function.name

            # Parse arguments from JSON string
            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError as e:
                _logger.error(
                    "Failed to decode tool arguments JSON",
                    error=str(e),
                    raw_args=tool_call.function.arguments,
                )
                return {
                    "success": False,
                    "detail": f"Invalid arguments format from LLM: {e}",
                    "error": "argument_parsing_error",
                }

            # Dispatch to handler via registry
            return self._dispatch_tool(func_name, args)

        except ConstitutionalViolationError as exc:
            _logger.warning(
                "Constitutional violation during execution",
                tool=func_name,
                error=str(exc),
            )
            return {
                "success": False,
                "detail": f"Constitutional violation: {exc.message}",
                "violation": exc.to_dict(),
            }
        except Exception as exc:
            _logger.exception("Execution step failed", tool=func_name)
            return {
                "success": False,
                "detail": f"Execution error in {func_name}: {exc}",
                "error": "tool_execution_error",
            }

    def execute_step(self, step: str) -> Dict[str, Any]:
        """Execute a single step using marker-based command format.

        Supports marker formats:
          - "semantic:find_files:dir=.:pattern=*.py" (semantic marker)
          - "composite:analyze_directory:dir=.:pattern=*.py" (composite marker)

        Args:
            step: Command string in marker format

        Returns:
            Dict with success/detail/data
        """
        try:
            # Parse command into (tool_name, args)
            tool_name, args = self._parser.parse(step)

            # Dispatch to handler
            return self._dispatch_tool(tool_name, args)

        except ValueError as e:
            _logger.warning("Failed to parse command", step=step, error=str(e))
            return {
                "success": False,
                "detail": str(e),
                "error": "invalid_command",
            }
        except Exception as e:
            _logger.exception("Step execution failed", step=step)
            return {
                "success": False,
                "detail": f"Execution error: {e}",
                "error": "execution_error",
            }

    def _dispatch_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch tool execution via registry with comprehensive error handling.

        Args:
            tool_name: Name of the tool to execute
            args: Arguments to pass to the tool

        Returns:
            Dict with execution results (always returns, never raises)
        """
        handler = self._tool_registry.get(tool_name)

        if not handler:
            _logger.warning("Unknown tool requested", tool=tool_name)
            # Provide helpful suggestions
            available_tools = list(self._tool_registry.keys())
            return {
                "success": False,
                "detail": f"Unsupported tool: {tool_name}. Available tools: {', '.join(available_tools[:5])}...",
                "error": "unknown_tool",
                "data": None,
            }

        try:
            _logger.debug("Executing tool", tool=tool_name, args=args)
            result = handler(**args)

            # Ensure result has required fields
            if not isinstance(result, dict):
                _logger.warning(
                    "Handler returned non-dict result",
                    tool=tool_name,
                    type=type(result),
                )
                result = {
                    "success": True,
                    "data": result,
                    "detail": "Operation completed",
                }

            # Ensure 'success' field exists
            if "success" not in result:
                result["success"] = True

            return result

        except ConstitutionalViolationError as exc:
            _logger.warning(
                "Constitutional violation during execution",
                tool=tool_name,
                error=str(exc),
            )
            return {
                "success": False,
                "detail": f"Constitutional violation: {exc.message}",
                "violation": exc.to_dict(),
                "data": None,
            }
        except TypeError as exc:
            # Likely argument mismatch
            _logger.error(
                "Tool argument error", tool=tool_name, args=args, error=str(exc)
            )
            return {
                "success": False,
                "detail": f"Invalid arguments for {tool_name}: {exc}",
                "error": "invalid_arguments",
                "data": None,
            }
        except Exception as exc:
            _logger.exception("Tool execution failed", tool=tool_name)
            return {
                "success": False,
                "detail": f"Tool error in {tool_name}: {type(exc).__name__}: {exc}",
                "error": "tool_execution_error",
                "data": None,
            }
