#!/usr/bin/env python3
"""Basic usage example for Prompt Registry."""

from pathlib import Path
from prompt_registry import PromptRegistry

def main():
    # Initialize registry with example prompts
    prompts_dir = Path(__file__).parent / "prompts"
    registry = PromptRegistry(prompts_dir)
    
    print("=== Prompt Registry Basic Usage ===\n")
    
    # List all prompts
    prompts = registry.list()
    print(f"Found {len(prompts)} prompts:")
    for prompt in prompts:
        print(f"  - {prompt.id}: {prompt.description}")
    
    print("\n=== Rendering a Prompt ===\n")
    
    # Get and render a prompt
    prompt = registry.get("data_analyst")
    if prompt:
        print(f"Prompt: {prompt.description}")
        print(f"Category: {prompt.category}")
        print(f"Variables: {prompt.variables}")
        
        # Render with variables
        rendered = registry.render("data_analyst", {
            "task": "analyze sales data trends",
            "format": "executive summary"
        })
        print(f"\nRendered prompt:\n{rendered}")
    
    print("\n=== Search Example ===\n")
    
    # Search prompts
    results = registry.search("data")
    print(f"Search results for 'data':")
    for prompt in results:
        print(f"  - {prompt.id}: {prompt.description}")
    
    print("\n=== Usage Tracking ===\n")
    
    # Report usage
    registry.report_usage("data_analyst", success=True, tokens_used=150)
    
    # Check updated stats
    updated_prompt = registry.get("data_analyst")
    print(f"Usage count: {updated_prompt.usage_count}")
    print(f"Success rate: {updated_prompt.success_rate:.2%}")
    print(f"Average tokens: {updated_prompt.avg_tokens_used}")

if __name__ == "__main__":
    main()
