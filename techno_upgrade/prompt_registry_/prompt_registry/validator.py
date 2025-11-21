"""Prompt validation utilities."""

import jsonschema
from typing import Dict, Any
from .models import Prompt


# JSON Schema for prompt validation
SCHEMA = {
    "type": "object",
    "required": ["id", "category", "prompt"],
    "properties": {
        "id": {"type": "string"},
        "category": {"type": "string"},
        "prompt": {"type": "string"},
        "description": {"type": "string"},
        "model": {"type": "string"},
        "variables": {
            "type": "array",
            "items": {"type": "string"}
        },
        "tags": {
            "type": "array", 
            "items": {"type": "string"}
        },
        "usage_count": {"type": "integer"},
        "last_used": {"type": "string", "format": "date-time"},
        "version": {"type": "string"},
        "rag_tags": {
            "type": "array",
            "items": {"type": "string"}
        },
        "intent_keywords": {
            "type": "array",
            "items": {"type": "string"}
        },
        "composable": {"type": "boolean"},
        "requires_context": {"type": "boolean"},
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "constraints": {
            "type": "array",
            "items": {"type": "string"}
        },
        "quality_score": {"type": "number"},
        "avg_tokens_used": {"type": "integer"},
        "success_rate": {"type": "number"},
        "last_optimized": {"type": "string", "format": "date-time"}
    }
}


def validate_prompt(data: Dict[str, Any]) -> bool:
    """Validate prompt data against schema."""
    try:
        jsonschema.validate(data, SCHEMA)
        return True
    except jsonschema.ValidationError as e:
        print(f"Validation error: {e.message}")
        return False
