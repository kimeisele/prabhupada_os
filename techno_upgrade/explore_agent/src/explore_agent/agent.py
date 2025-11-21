"""ExploreAgent implements a plan-execute-synthesize loop."""

import datetime as dt
from typing import Any, Dict, List, Optional

from .dependencies import LLMProvider, get_logger
from .actions import ActionExecutor
from .context import ContextManager
from .planning import Planner


MAX_GOAL_LENGTH = 500
DISALLOWED_GOAL_KEYWORDS = {"exploit", "destruct", "exfiltrate"}
MAX_FINDING_SIZE = 100_000

_logger = get_logger("phoenix.explore_agent")


class ExploreAgent:
    """Autonomous agent that iteratively explores the codebase."""

    def __init__(
        self,
        api: Any,
        llm_provider: LLMProvider,
    ):
        if api is None:
            raise ValueError("Agent API instance is required")
        if llm_provider is None:
            raise ValueError("LLM provider is required")

        self._api = api
        self._action_executor = ActionExecutor(api)
        self._planner = Planner(llm_provider)
        self._context_manager = ContextManager()
        self._history: List[Dict[str, Any]] = []
        self._original_goal: Optional[str] = None

    @property
    def execution_history(self) -> List[Dict[str, Any]]:
        """Get the execution history of the agent."""
        return self._history

    def run(self, goal: str, max_iterations: int = 10) -> str:
        """
        Execute the iterative Plan-Execute-Reflect loop.

        This method coordinates the exploration process:
        1. Plan: Ask LLM for next step(s) based on goal + accumulated context
        2. Execute: Run the tool(s) via ActionExecutor
        3. Reflect: Update context and check if goal is met
        4. Repeat until goal met or max_iterations reached
        """
        self._prepare_run(goal)

        for iteration in range(1, max_iterations + 1):
            context_for_llm = self._context_manager.get_planning_context()

            # Get next steps from planner (can be ToolCall objects or strings)
            steps = self._planner.get_next_steps(goal, context_for_llm)
            self._record_event(
                "plan",
                iteration,
                f"Generated {len(steps)} steps",
                metadata={"steps": self._serialize_steps(steps)},
            )

            if not steps:
                _logger.info("LLM returned no steps, assuming goal is met.")
                break

            # Execute step(s) - handle both ToolCall objects and string commands
            step = steps[0]

            # Check if this is a ToolCall object (from Mistral) or string command
            if hasattr(step, "function"):
                # ToolCall object from Mistral
                result = self._action_executor.execute_tool_call(step)
                step_description = f"{step.function.name}({step.function.arguments})"
            else:
                # String command (marker format or legacy)
                result = self._action_executor.execute_step(step)
                step_description = str(step)

            self._record_event(
                "execute", iteration, step_description, success=result.get("success")
            )

            self._context_manager.update_context(step_description, result)
            self._record_event(
                "synthesize", iteration, "Result accumulated into context"
            )

        return self._finalize_run()

    def _serialize_steps(self, steps):
        """Serialize steps for logging (handles both strings and ToolCall objects)."""
        serialized = []
        for step in steps:
            if hasattr(step, "function"):
                serialized.append(f"{step.function.name}({step.function.arguments})")
            else:
                serialized.append(str(step))
        return serialized

    def _prepare_run(self, goal: str):
        """Sanitizes the goal and resets the agent's state for a new run."""
        if not goal or not goal.strip():
            raise ValueError("Goal must be a non-empty string")

        cleaned_goal = goal.strip()
        if any(keyword in cleaned_goal.lower() for keyword in DISALLOWED_GOAL_KEYWORDS):
            raise ValueError("Goal violates safety constraints")

        if len(cleaned_goal) > MAX_GOAL_LENGTH:
            _logger.warning(
                "Goal truncated for safety", original_length=len(cleaned_goal)
            )
            cleaned_goal = cleaned_goal[:MAX_GOAL_LENGTH]

        self._original_goal = cleaned_goal
        self._history.clear()
        self._context_manager = ContextManager()  # Reset context
        self._record_event("start", 0, "Exploration run started")

    def _finalize_run(self) -> str:
        """Builds and returns the final summary report of the run."""
        timestamp = dt.datetime.utcnow().replace(microsecond=0, tzinfo=dt.UTC)
        summary = self._build_summary(timestamp)
        self._record_event("complete", len(self._history), "Run completed")
        # In a real system, this summary would be saved, indexed, etc.
        return summary

    def _build_summary(self, timestamp: dt.datetime) -> str:
        """Constructs the final markdown summary with intelligent status detection."""
        # Determine status based on execution history
        status = self._determine_status()

        lines = [
            f"# Exploration: {self._original_goal}",
            "",
            "## Metadata",
            f"- Status: {status}",
            f"- Timestamp: {timestamp.isoformat()}",
            f"- Iterations: {self._count_iterations()}",
            "",
            "## Summary",
            self._context_manager.get_planning_context() or "No findings recorded.",
            "",
            "## Execution History",
        ]
        for event in self._history:
            lines.append(
                f"- `[{event.get('timestamp')}]` **{event.get('phase')}**: {event.get('detail')}"
            )

        return "\n".join(lines).strip()

    def _determine_status(self) -> str:
        """Determine exploration status based on execution history."""
        # Check if there are any failed executions
        execute_events = [e for e in self._history if e.get("phase") == "execute"]
        if not execute_events:
            return "INCOMPLETE"

        # Check if all executions succeeded
        all_success = all(e.get("success", False) for e in execute_events)

        # Check if LLM signaled completion (no more steps)
        plan_events = [e for e in self._history if e.get("phase") == "plan"]
        if plan_events:
            last_plan = plan_events[-1]
            steps = last_plan.get("metadata", {}).get("steps", [])
            if not steps:
                return "COMPLETED"

        # If we have successful executions but didn't finish naturally, mark as incomplete
        if execute_events and not all_success:
            return "INCOMPLETE"

        return "COMPLETED" if all_success else "INCOMPLETE"

    def _count_iterations(self) -> int:
        """Count the number of iterations executed."""
        return len([e for e in self._history if e.get("phase") == "execute"])

    def _record_event(
        self,
        phase: str,
        iteration: int,
        detail: str,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Records an event to the agent's history."""
        event = {
            "timestamp": dt.datetime.utcnow().isoformat(),
            "phase": phase,
            "iteration": iteration,
            "detail": detail,
            "success": success,
            "metadata": metadata or {},
        }
        self._history.append(event)


__all__ = ["ExploreAgent", "MAX_GOAL_LENGTH", "MAX_FINDING_SIZE"]
