"""External dependency interfaces for ExploreAgent.

This module provides abstract interfaces for external dependencies
that ExploreAgent needs. This allows the package to work standalone
while accepting these dependencies from outside.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


# ============================================================================
# LLM Provider Interface
# ============================================================================

class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> str:
        """Generate a completion for the given prompt."""
        pass

    @abstractmethod
    def chat(self, messages: list, **kwargs) -> str:
        """Generate a chat response for the given messages."""
        pass


# ============================================================================
# Logger Interface
# ============================================================================

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    This is a simple wrapper around logging.getLogger that can be
    overridden if you have a custom logging setup.
    """
    return logging.getLogger(name)


# ============================================================================
# Error Types
# ============================================================================

class ConstitutionalViolationError(Exception):
    """Raised when a constitutional safety check fails."""
    pass


__all__ = [
    "LLMProvider",
    "get_logger",
    "ConstitutionalViolationError",
]
