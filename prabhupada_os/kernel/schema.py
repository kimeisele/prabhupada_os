import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Type, TypeVar

T = TypeVar("T")

@dataclass
class InputSchema:
    """
    Schema for input to the Kernel.
    Strictly defines what the Kernel accepts.
    """
    query: str
    filter_metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if not isinstance(self.query, str):
            raise ValueError("Field 'query' must be a string.")
        if len(self.query) > 1000:
             raise ValueError("Field 'query' exceeds maximum length of 1000 characters.")
        if self.filter_metadata is not None and not isinstance(self.filter_metadata, dict):
            raise ValueError("Field 'filter_metadata' must be a dictionary.")

@dataclass
class OutputSchema:
    """
    Schema for output from the Kernel.
    Strictly defines what the Kernel returns.
    """
    result: str
    metadata: Dict[str, Any]
    error: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

def validate_input(data: Dict[str, Any]) -> InputSchema:
    """
    Validates a dictionary against the InputSchema.
    Raises ValueError if validation fails.
    """
    # Filter out extra keys to be strict, or allow them but ignore?
    # For security, we should probably only pass known keys or just let dataclass handle it if we unpack.
    # However, dataclass constructor will fail with unexpected args if we just unpack.
    # Let's do a safe unpack.
    
    known_keys = InputSchema.__annotations__.keys()
    filtered_data = {k: v for k, v in data.items() if k in known_keys}
    
    # Check for missing required keys (dataclass won't catch missing non-default args if we don't pass them)
    # But here we are passing filtered_data.
    
    try:
        return InputSchema(**filtered_data)
    except TypeError as e:
        raise ValueError(f"Schema validation error: {e}")
