"""
GAD-3: AGENT FRAMEWORK

The active agents (Legs) that utilize the infrastructure (Body, Brain, Arms).

Classes:
  - BaseAgent: The integration hub connecting Runtime, Knowledge, and Mission Control
"""

from .base_agent import BaseAgent, ExecutionResult, KnowledgeResult

__all__ = ["BaseAgent", "ExecutionResult", "KnowledgeResult"]
