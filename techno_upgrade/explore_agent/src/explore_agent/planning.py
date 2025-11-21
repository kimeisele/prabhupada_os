"""Handles all planning logic for the ExploreAgent."""

from typing import Any, Dict, List, Tuple

from .dependencies import get_logger
from .actions import CommandParser


_logger = get_logger("phoenix.explore_agent.planning")


class Planner:
    """
    Handles the generation and parsing of execution plans for the ExploreAgent.
    It integrates with the LLM to get the next steps and translates them into
    executable commands.
    """

    def __init__(self, llm_provider: Any):
        self._llm = llm_provider
        self._parser = CommandParser()

    def get_next_steps(self, goal: str, context: str, max_steps: int = 5) -> List[Any]:
        """
        Given a goal and the current context, generate the next steps.

        Args:
            goal: The overall objective.
            context: The accumulated context from previous steps.
            max_steps: The maximum number of steps to generate.

        Returns:
            A list of steps - can be strings (marker format) or ToolCall objects (from Mistral)
        """
        try:
            plan_result = self._llm.generate_plan(goal, context)

            if not plan_result:
                _logger.info("LLM returned no new steps, assuming goal is met.")
                return []

            # Handle different return types from various LLM providers
            if isinstance(plan_result, list):
                # Could be list of strings, ToolCall objects, or empty
                if not plan_result:
                    return []

                # Return as-is if list - caller will handle different types
                # This supports both string commands and ToolCall objects
                return plan_result

            if isinstance(plan_result, str):
                # String-based plan (from LocalDeterministicProvider or text-based LLMs)
                steps = self._parse_plan_string(plan_result)
                return steps

            # Unknown type - try to convert to string and parse
            _logger.warning(
                "LLM returned unexpected type for plan, attempting conversion",
                type=type(plan_result).__name__,
            )
            return self._parse_plan_string(str(plan_result))

        except Exception as e:
            _logger.error(
                "Failed to generate plan from LLM", error=str(e), exc_info=True
            )
            # Return empty list instead of error string - let agent handle gracefully
            return []

    def parse_step(self, step: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse a single command string into a tool name and arguments.
        """
        return self._parser.parse(step)

    def _build_plan_prompt(self, goal: str, context: str, max_steps: int) -> str:
        """Builds the prompt for the LLM to generate the next steps."""
        # This prompt would be much more sophisticated in a real system,
        # including examples, constraints, and available tools.
        return f"""
        Given the overall goal:
        ---
        {goal}
        ---

        And the context from previous steps:
        ---
        {context}
        ---

        Generate the next {max_steps} steps to achieve the goal.
        Each step must be a valid command in the format:
        'semantic:tool_name:key1=value1:key2=value2'

        Return the plan as a Python list of strings.
        """

    def _parse_plan_string(self, plan_str: str) -> List[str]:
        """Parses a string that represents a list of commands.

        Handles multiple formats:
        - JSON array: '["step1", "step2"]'
        - Numbered list: '1. step1\n2. step2'
        - Line-separated: 'step1\nstep2'
        """
        plan_str = plan_str.strip()

        if not plan_str:
            return []

        # Try JSON array format first
        if plan_str.startswith("[") and plan_str.endswith("]"):
            try:
                import ast

                # Use ast.literal_eval for safe parsing
                parsed = ast.literal_eval(plan_str)
                if isinstance(parsed, list):
                    return [str(s).strip() for s in parsed if s]
            except Exception as e:
                _logger.debug("Failed to parse as JSON array", error=str(e))

        # Try numbered list format (1. step, 2. step, etc.)
        import re

        numbered_pattern = r"^\d+\.\s+(.+)$"
        lines = plan_str.split("\n")
        numbered_steps = []
        for line in lines:
            match = re.match(numbered_pattern, line.strip())
            if match:
                numbered_steps.append(match.group(1).strip())

        if numbered_steps:
            return numbered_steps

        # Fallback: split by newlines and filter empty
        steps = [s.strip() for s in lines if s.strip()]
        return steps if steps else [plan_str]
