from pathlib import Path
from typing import List, Optional
import json
from .models import Prompt
from datetime import datetime
from .context_injector import ContextInjector


class PromptRegistry:
    def __init__(self, prompts_dir: Path, context_providers: dict = None):
        self.prompts_dir = prompts_dir
        self.prompts: dict[str, Prompt] = {}
        self.context_injector = ContextInjector(context_providers)
        self._load_all()

    def _load_all(self):
        """Load all JSON prompts from directory."""
        for json_file in self.prompts_dir.rglob("*.json"):
            if json_file.name == "schema.json":
                continue  # Skip schema file

            try:
                with open(json_file) as f:
                    data = json.load(f)
                prompt = Prompt.from_json(data)
                self.prompts[prompt.id] = prompt
            except Exception as e:
                print(f"Warning: Failed to load {json_file}: {e}")

    def get(self, prompt_id: str) -> Optional[Prompt]:
        """Get prompt by ID."""
        return self.prompts.get(prompt_id)

    def list(
        self, category: Optional[str] = None, tag: Optional[str] = None
    ) -> List[Prompt]:
        """List prompts, optionally filtered."""
        results = list(self.prompts.values())

        if category:
            results = [p for p in results if p.category == category]

        if tag:
            results = [p for p in results if tag in p.tags]

        return sorted(results, key=lambda p: p.id)

    def search(self, query: str) -> List[Prompt]:
        """Search prompts by text (id, description, tags, prompt content)."""
        query_lower = query.lower()
        results = []

        for prompt in self.prompts.values():
            if (
                query_lower in prompt.id.lower()
                or query_lower in prompt.description.lower()
                or query_lower in prompt.prompt.lower()
                or any(query_lower in tag.lower() for tag in prompt.tags)
            ):
                results.append(prompt)

        return results

    def render(self, prompt_id: str, variables: dict[str, str]) -> str:
        """Render prompt with context injection and variable substitution."""
        prompt = self.get(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt not found: {prompt_id}")

        # Use ContextInjector to inject context and substitute variables
        rendered = self.context_injector.inject(prompt, variables)

        return rendered

    def report_usage(
        self, prompt_id: str, success: bool, tokens_used: Optional[int] = None
    ):
        """Report the usage of a prompt and update its quality metrics."""
        prompt = self.get(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt not found: {prompt_id}")

        # Update usage count and last used time
        prompt.usage_count += 1
        prompt.last_used = datetime.now()

        # Update success rate
        if prompt.success_rate is None:
            prompt.success_rate = 1.0 if success else 0.0
        else:
            prompt.success_rate = (
                (prompt.success_rate * (prompt.usage_count - 1)) + (1 if success else 0)
            ) / prompt.usage_count

        # Update average tokens used
        if tokens_used is not None:
            if prompt.avg_tokens_used is None:
                prompt.avg_tokens_used = tokens_used
            else:
                prompt.avg_tokens_used = (
                    (prompt.avg_tokens_used * (prompt.usage_count - 1)) + tokens_used
                ) / prompt.usage_count

        # Placeholder for quality score calculation
        if prompt.success_rate is not None:
            prompt.quality_score = prompt.success_rate  # Simple initial implementation

        self._save_prompt(prompt)

    def _save_prompt(self, prompt: Prompt):
        """Save updated prompt (for usage tracking)."""
        # Find original file
        for json_file in self.prompts_dir.rglob("*.json"):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                if data.get("id") == prompt.id:
                    with open(json_file, "w") as f:
                        json.dump(prompt.to_json(), f, indent=2)
                    return
            except:
                pass
