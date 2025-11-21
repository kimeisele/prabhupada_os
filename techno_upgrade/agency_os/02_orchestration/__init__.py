"""Orchestration Layer (GAD-2): The Control Nexus

Coordinates delivery, task management, and atomic Git operations.
This layer ensures agents never have to worry about Git mechanics.
"""

from .task_executor import TaskExecutor

__all__ = ["TaskExecutor"]
