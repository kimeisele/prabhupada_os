# ExploreAgent - Autonomous Codebase Exploration

A standalone Python package for autonomous codebase exploration using a plan-execute-synthesize loop.

## Features

- **Plan-Execute-Synthesize Loop**: Iterative exploration with LLM-driven planning
- **Temporary RAG Store**: Efficient context management with embeddings
- **Tool Abstractions**: Extensible tool system for filesystem, code search, shell execution, and analysis
- **Safety Constraints**: Built-in goal validation and safety checks
- **Execution History**: Detailed tracking of all exploration steps

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from explore_agent import ExploreAgent, LLMProvider

# Implement LLMProvider interface for your LLM backend
class MyLLMProvider(LLMProvider):
    def complete(self, prompt: str, **kwargs) -> str:
        # Your LLM implementation here
        pass

    def chat(self, messages: list, **kwargs) -> str:
        # Your chat implementation here
        pass

# Create and run the agent
llm = MyLLMProvider()
agent = ExploreAgent(api=your_api_instance, llm_provider=llm)

result = agent.run(
    goal="understand authentication flow",
    max_iterations=5
)

print(result)
```

## Components

### ExploreAgent
Main agent class that orchestrates the exploration loop.

**Parameters:**
- `api`: Agent API instance with tool execution capabilities
- `llm_provider`: LLMProvider implementation for planning

**Methods:**
- `run(goal, max_iterations)`: Execute exploration loop
- `execution_history`: Get detailed history of all steps

### LLMProvider (Interface)
Abstract base class for LLM implementations.

**Methods:**
- `complete(prompt, **kwargs)`: Generate text completion
- `chat(messages, **kwargs)`: Generate chat response

### Helper Classes

- **ActionExecutor**: Executes exploration actions (filesystem, search, analysis)
- **ContextManager**: Manages exploration context with RAG
- **Planner**: Generates next steps based on goal and context
- **Handlers**: Specialized handlers for different tool types
  - FilesystemHandler
  - SearchHandler
  - AnalysisHandler
  - ShellHandler

## Dependencies

Core dependencies are minimal:
- `typing-extensions>=4.0` (for type hints)

You'll need to provide:
- An implementation of `LLMProvider` interface
- An API instance with tool execution capabilities

## Configuration

### Logger
By default, uses Python's standard logging. Override with custom logger:

```python
from explore_agent.dependencies import get_logger

# Configure logging as needed
import logging
logging.basicConfig(level=logging.INFO)
```

## Safety Features

- **Goal Validation**: Prevents harmful exploration goals
- **Max Context**: Limits context length to prevent memory issues
- **Constitutional Checks**: Validates actions against safety constraints

## License

Extracted from Phoenix System
