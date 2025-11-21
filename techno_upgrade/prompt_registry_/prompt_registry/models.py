from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Prompt:
    id: str
    category: str  # agent_primers, expert_personas, task_templates, project_context
    prompt: str
    description: str = ""
    model: Optional[str] = None  # e.g., "chatgpt-4", "claude-sonnet"
    variables: List[str] = field(default_factory=list)  # ["task", "deliverables"]
    tags: List[str] = field(default_factory=list)
    usage_count: int = 0
    last_used: Optional[datetime] = None

    # New fields for Semantic Enhancement (Layer 2)
    version: str = "1.0"
    rag_tags: List[str] = field(default_factory=list)
    intent_keywords: List[str] = field(default_factory=list)
    composable: bool = False
    requires_context: bool = False  # For Context Injection System
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    constraints: List[str] = field(default_factory=list)

    # New fields for Intelligence Layer (Layer 3)
    quality_score: Optional[float] = None
    avg_tokens_used: Optional[int] = None
    success_rate: Optional[float] = None
    last_optimized: Optional[datetime] = None

    @classmethod
    def from_json(cls, data: dict) -> "Prompt":
        """Load from JSON file."""
        return cls(
            id=data["id"],
            category=data["category"],
            prompt=data["prompt"],
            description=data.get("description", ""),
            model=data.get("model"),
            variables=data.get("variables", []),
            tags=data.get("tags", []),
            usage_count=data.get("usage_count", 0),
            last_used=datetime.fromisoformat(data["last_used"])
            if data.get("last_used")
            else None,
            version=data.get("version", "1.0"),
            rag_tags=data.get("rag_tags", []),
            intent_keywords=data.get("intent_keywords", []),
            composable=data.get("composable", False),
            requires_context=data.get("requires_context", False),
            input_schema=data.get("input_schema"),
            output_schema=data.get("output_schema"),
            constraints=data.get("constraints", []),
            quality_score=data.get("quality_score"),
            avg_tokens_used=data.get("avg_tokens_used"),
            success_rate=data.get("success_rate"),
            last_optimized=datetime.fromisoformat(data["last_optimized"])
            if data.get("last_optimized")
            else None,
        )

    def to_json(self) -> dict:
        """Save to JSON file."""
        return {
            "id": self.id,
            "category": self.category,
            "prompt": self.prompt,
            "description": self.description,
            "model": self.model,
            "variables": self.variables,
            "tags": self.tags,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "version": self.version,
            "rag_tags": self.rag_tags,
            "intent_keywords": self.intent_keywords,
            "composable": self.composable,
            "requires_context": self.requires_context,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "constraints": self.constraints,
            "quality_score": self.quality_score,
            "avg_tokens_used": self.avg_tokens_used,
            "success_rate": self.success_rate,
            "last_optimized": self.last_optimized.isoformat()
            if self.last_optimized
            else None,
        }
