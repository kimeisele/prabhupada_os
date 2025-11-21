"""Analysis handler for explore agent actions."""

from typing import Any, Dict

from ..dependencies import get_logger
from ..tool_abstractions import CodeAnalyzer


_logger = get_logger("phoenix.explore_agent.handlers.analysis")


class AnalysisHandler:
    """Handles code analysis operations with multi-analysis support."""

    def __init__(self, api: Any):
        """Initialize analysis handler.

        Args:
            api: Agent API instance
        """
        if api is None:
            raise ValueError("Agent API instance is required")
        self._api = api
        self._code_analyzer = CodeAnalyzer(api)

    def analyze_python(
        self, file_path: str, analysis_type: str = "all"
    ) -> Dict[str, Any]:
        """Analyze Python file combining multiple analysis types.

        Args:
            file_path: Path to Python file to analyze
            analysis_type: Type of analysis (functions, classes, imports, all)

        Returns:
            Dict with success/detail/data containing combined results
        """
        result = {}

        if analysis_type in ("functions", "all"):
            result.update(self._code_analyzer.find_functions(file_path))

        if analysis_type in ("classes", "all"):
            classes_result = self._code_analyzer.find_classes(file_path)
            if classes_result["success"]:
                result["classes"] = classes_result.get("classes", [])

        if analysis_type in ("imports", "all"):
            imports_result = self._code_analyzer.find_imports(file_path)
            if imports_result["success"]:
                result["imports"] = imports_result.get("imports", [])

        # Return combined results
        if result:
            return {
                "success": True,
                "data": result,
                "detail": f"Analyzed {file_path}: {len(result.get('classes', []))} classes found",
                **result,
            }
        else:
            return {
                "success": False,
                "data": [],
                "detail": f"Analysis type '{analysis_type}' not recognized",
                "error": "invalid_analysis_type",
            }
