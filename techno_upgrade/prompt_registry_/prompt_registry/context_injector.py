"""Context Injection System for Prompts."""

import json
from typing import Dict, Any
from .models import Prompt


class ContextInjector:
    """Adds context to prompts."""

    def __init__(self, context_providers: Dict[str, Any] = None):
        """Initialize with optional context providers."""
        self.context_providers = context_providers or {}

    def inject(self, prompt: Prompt, variables: dict) -> str:
        """Injects context into a prompt and substitutes variables."""
        base = prompt.prompt

        # Add custom context if required
        if prompt.requires_context:
            context = self._get_context(prompt.category)
            if context:
                base = f"CONTEXT:\n{context}\n\n{base}"

        # Variable substitution
        rendered = self._substitute(base, variables)
        return rendered

    def _get_context(self, category: str) -> str:
        """Get context for a specific category."""
        if category in self.context_providers:
            provider = self.context_providers[category]
            if callable(provider):
                return provider()
            return str(provider)
        return ""

    def _substitute(self, text: str, variables: dict) -> str:
        """Substitutes variables in the format ${variable}."""
        for var, value in variables.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            text = text.replace(f"${{{var}}}", str(value))
        return text
