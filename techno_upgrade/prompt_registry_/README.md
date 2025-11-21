# Prompt Registry

A flexible and extensible prompt registry system for managing AI prompts in Python projects.

## Features

- **Prompt Management**: Store, organize, and retrieve AI prompts with metadata
- **Variable Substitution**: Dynamic prompt rendering with context variables
- **Context Injection**: Automatic context injection for different prompt categories
- **Usage Tracking**: Monitor prompt performance and usage statistics
- **Search & Filter**: Find prompts by category, tags, or text search
- **JSON-based Storage**: Human-readable prompt definitions
- **Extensible**: Easy to customize for different use cases

## Installation

```bash
pip install prompt-registry
```

For development:
```bash
pip install prompt-registry[dev]
```

## Quick Start

```python
from pathlib import Path
from prompt_registry import PromptRegistry, Prompt

# Initialize registry with a directory containing JSON prompt files
registry = PromptRegistry(Path("./prompts"))

# List all prompts
prompts = registry.list()
print(f"Found {len(prompts)} prompts")

# Get a specific prompt
prompt = registry.get("my_prompt_id")
if prompt:
    print(f"Prompt: {prompt.description}")

# Render prompt with variables
rendered = registry.render("my_prompt_id", {"task": "analyze data", "format": "json"})
print(rendered)

# Search prompts
results = registry.search("data analysis")
for prompt in results:
    print(f"Found: {prompt.id} - {prompt.description}")
```

## Prompt Format

Prompts are stored as JSON files:

```json
{
  "id": "data_analyst",
  "category": "expert_personas",
  "prompt": "You are an expert data analyst. Task: ${task}. Format: ${format}.",
  "description": "Expert data analyst persona for data analysis tasks",
  "model": "gpt-4",
  "variables": ["task", "format"],
  "tags": ["analysis", "data", "expert"],
  "requires_context": false,
  "composable": true
}
```

## Advanced Usage

### Custom Context Providers

```python
def get_system_context():
    return "Current system status: All systems operational"

context_providers = {
    "system_status": get_system_context
}

registry = PromptRegistry(
    prompts_dir=Path("./prompts"),
    context_providers=context_providers
)
```

### Usage Tracking

```python
# Report prompt usage for analytics
registry.report_usage(
    prompt_id="data_analyst",
    success=True,
    tokens_used=150
)

# Get performance metrics
prompt = registry.get("data_analyst")
print(f"Success rate: {prompt.success_rate:.2%}")
print(f"Average tokens: {prompt.avg_tokens_used}")
```

### Programmatic Prompt Creation

```python
from datetime import datetime

new_prompt = Prompt(
    id="custom_analyzer",
    category="task_templates",
    prompt="Analyze the following data: ${data}",
    description="Custom data analysis template",
    variables=["data"],
    tags=["analysis", "custom"],
    version="1.0"
)

# Save to registry (manual JSON file creation required)
```

## Directory Structure

```
prompts/
├── expert_personas/
│   ├── data_analyst.json
│   └── code_reviewer.json
├── task_templates/
│   ├── analyze_data.json
│   └── generate_report.json
└── project_context/
    └── system_info.json
```

## API Reference

### PromptRegistry

- `__init__(prompts_dir, context_providers=None)`: Initialize registry
- `get(prompt_id)`: Get prompt by ID
- `list(category=None, tag=None)`: List prompts with optional filters
- `search(query)`: Search prompts by text
- `render(prompt_id, variables)`: Render prompt with variables
- `report_usage(prompt_id, success, tokens_used=None)`: Track usage

### Prompt

Dataclass with fields:
- `id`: Unique identifier
- `category`: Prompt category
- `prompt`: Prompt template text
- `description`: Human-readable description
- `variables`: List of variable names
- `tags`: Search tags
- `usage_count`: Usage statistics
- `quality_score`: Performance metrics
- And more...

## Development

```bash
# Clone repository
git clone https://github.com/your-username/prompt-registry.git
cd prompt-registry

# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Run linting
black prompt_registry/
flake8 prompt_registry/
mypy prompt_registry/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Changelog

### 1.0.0
- Initial release
- Core prompt registry functionality
- JSON-based prompt storage
- Variable substitution and context injection
- Usage tracking and analytics
- Search and filtering capabilities
