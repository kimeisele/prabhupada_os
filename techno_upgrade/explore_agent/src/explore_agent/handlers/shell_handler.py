"""Shell handler for explore agent actions."""

from typing import Any, Dict

from ..dependencies import get_logger


_logger = get_logger("phoenix.explore_agent.handlers.shell")


class ShellHandler:
    """Handles shell command execution with API validation."""

    def __init__(self, api: Any):
        """Initialize shell handler.

        Args:
            api: Agent API instance
        """
        if api is None:
            raise ValueError("Agent API instance is required")
        self._api = api

    def run(self, command: str) -> Dict[str, Any]:
        """Run shell command with API validation.

        Args:
            command: Shell command to execute

        Returns:
            Dict with success/detail/data
        """
        system_api = getattr(self._api, "system", None)
        if system_api is None:
            return {
                "success": False,
                "detail": "System API is unavailable",
                "error": "api_unavailable",
            }

        if not command:
            return {
                "success": False,
                "detail": "Shell command is empty",
                "error": "missing_argument",
            }

        try:
            result = system_api.run_shell_command(command)
            success = result.get("exit_code", 1) == 0
            return {
                "success": success,
                "detail": f"Command exited with {result.get('exit_code')}",
                "data": result,
                "type": "system.run_shell_command",
            }
        except TimeoutError:
            _logger.warning("Shell command timed out", command=command)
            return {
                "success": False,
                "detail": f"Command timeout: {command}",
                "error": "timeout",
            }
        except Exception as exc:
            _logger.warning("Shell command failed", command=command, error=str(exc))
            return {
                "success": False,
                "detail": f"Command error: {exc}",
                "error": "command_error",
            }
