"""Manages the context for the ExploreAgent."""

from typing import Any, Dict, List

from .dependencies import get_logger


_logger = get_logger("phoenix.explore_agent.context")

# A simple, arbitrary limit to prevent infinite context growth.
MAX_CONTEXT_LENGTH = 32000


class ContextManager:
    """
    Builds and manages the context for the agent's planning process.
    It accumulates findings and summarizes results to keep the context concise.

    Key responsibilities:
    - Accumulate step results in a structured way
    - Prevent context explosion via truncation and summarization
    - Provide formatted context for LLM planning
    """

    def __init__(self):
        self._accumulated_context: List[str] = []
        self._step_count = 0
        self._success_count = 0
        self._failure_count = 0

    def get_planning_context(self) -> str:
        """Returns the current accumulated context as a single string."""
        if not self._accumulated_context:
            return ""

        # Add summary statistics at the beginning
        stats = f"Steps executed: {self._step_count} (✓ {self._success_count}, ✗ {self._failure_count})"
        return f"{stats}\n\n" + "\n".join(self._accumulated_context)

    def update_context(self, step: str, result: Dict[str, Any]):
        """
        Summarizes the result of a step and adds it to the context.
        """
        self._step_count += 1
        if result.get("success"):
            self._success_count += 1
        else:
            self._failure_count += 1

        summary = self._summarize_step_result(step, result)
        self._accumulated_context.append(summary)

        # Truncate context if it gets too long
        current_length = len(self.get_planning_context())
        if current_length > MAX_CONTEXT_LENGTH:
            _logger.warning(
                "Context length is exceeding limit, truncating oldest entries."
            )
            # Remove oldest entries but keep at least the last 3
            if len(self._accumulated_context) > 3:
                self._accumulated_context.pop(0)

    def _summarize_step_result(self, step: str, result: Dict[str, Any]) -> str:
        """
        Creates a concise summary of a step's execution result.
        """
        if result.get("success"):
            detail = result.get("detail", "Step executed successfully.")
            # Avoid adding large data blobs to the context
            if "data" in result:
                data = result["data"]
                if isinstance(data, list):
                    # For lists, show first few items if they're small structured data
                    if len(data) <= 10 and all(isinstance(item, dict) for item in data):
                        import json

                        data_summary = f"\n{json.dumps(data, indent=2)}"
                    else:
                        # Show first 20 items even if list is long - LLM needs to see actual data
                        data_summary = f" (showing first 20/{len(data)})\n"
                        import json

                        sample = data[:20] if len(data) > 20 else data
                        data_summary += json.dumps(sample, indent=2)
                elif isinstance(data, dict):
                    # For dicts, always show key file paths info
                    import json

                    # Special handling for search results
                    if "matching_files" in data:
                        files = data["matching_files"][:20]  # Show first 20
                        data_summary = f"\nMatching files ({len(data.get('matching_files', []))} total):\n"
                        data_summary += json.dumps(files, indent=2)
                    elif "files" in data:
                        files = data["files"][:20]  # Show first 20
                        data_summary = (
                            f"\nFiles found ({len(data.get('files', []))} total):\n"
                        )
                        data_summary += json.dumps(files, indent=2)
                    else:
                        data_json = json.dumps(data, indent=2)
                        if len(data_json) < 2000:  # Increased from 1000
                            data_summary = f"\n{data_json}"
                        else:
                            data_summary = f" ({len(data)} keys, truncated)"
                elif isinstance(data, str):
                    # Include string data but truncate if too long
                    max_data_len = 10000
                    if len(data) > max_data_len:
                        data_summary = f"\nData: {data[:max_data_len]}... (truncated)"
                    else:
                        data_summary = f"\nData: {data}"
                else:
                    data_summary = ""
            else:
                data_summary = ""
            return f"Executed: `{step}` -> {detail}{data_summary}"
        else:
            error = result.get("error", "unknown_error")
            detail = result.get("detail", "Step failed.")
            return f"Failed: `{step}` -> Error: {error}. Detail: {detail}"
