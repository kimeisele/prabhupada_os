import yaml
import json
import os
import sys

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "cortex", "knowledge")

# Map of keys to file paths
SCHEMA_MAP = {
    "sambandha": os.path.join(KNOWLEDGE_DIR, "theology", "sambandha.yaml"),
    "abhidheya": os.path.join(KNOWLEDGE_DIR, "theology", "abhidheya.yaml"),
    "prayojana": os.path.join(KNOWLEDGE_DIR, "theology", "prayojana.yaml"),
    "adhikara": os.path.join(KNOWLEDGE_DIR, "logic", "adhikara.yaml"),
    "virodha": os.path.join(KNOWLEDGE_DIR, "logic", "virodha.yaml"),
    "shastra_map": os.path.join(KNOWLEDGE_DIR, "navigation", "shastra_map.yaml"),
    "persona": os.path.join(KNOWLEDGE_DIR, "interface", "persona.yaml"),
}

def load_yaml(path):
    """Load a YAML file and return its content."""
    if not os.path.exists(path):
        print(f"Warning: File not found: {path}")
        return {}
    
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        print(f"Error parsing {path}: {e}")
        return {}

def build_knowledge_context():
    """Load all schema files and merge into a single context object."""
    context = {}
    
    print("Loading Knowledge Hypercube...")
    for key, path in SCHEMA_MAP.items():
        print(f"  - Loading {key}...")
        data = load_yaml(path)
        context[key] = data
        
    return context

def main():
    context = build_knowledge_context()
    
    # Validation: Check if virodha rule exists
    rules = context.get("virodha", {}).get("rules", [])
    if rules:
        print(f"\n[Validation] Found {len(rules)} Virodha rule(s).")
        print(f"  - Rule 1: {rules[0].get('name')}")
    else:
        print("\n[Validation] No Virodha rules found.")
        
    # Output JSON for inspection
    print("\n[Graph Context Merged]")
    print(json.dumps(context, indent=2))

if __name__ == "__main__":
    main()
