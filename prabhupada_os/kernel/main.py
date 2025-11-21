import sys
import json
import traceback
from typing import Dict, Any

# Import local modules
# We need to ensure the current directory is in path if running directly, 
# but typically this is run as a module or with PYTHONPATH set. 
# For simplicity in this script, we assume it's run from the root or we add path.
# However, relative imports might be tricky if run as script. 
# Let's try absolute imports assuming package structure or just local if same dir.

try:
    from schema import validate_input, OutputSchema
    from logic import search
except ImportError:
    # Fallback for running directly inside the directory
    from .schema import validate_input, OutputSchema
    from .logic import search

def main():
    """
    Main entry point.
    Reads JSON from STDIN.
    Validates input.
    Executes logic.
    Writes JSON to STDOUT.
    """
    try:
        # 1. Read from STDIN
        input_str = sys.stdin.read()
        if not input_str.strip():
            # Empty input
            return

        try:
            input_data = json.loads(input_str)
        except json.JSONDecodeError:
            error_out("Invalid JSON input.")
            return

        # 2. Validate Input
        try:
            validated_input = validate_input(input_data)
        except ValueError as e:
            error_out(str(e))
            return

        # 3. Execute Logic
        results = search(validated_input.query)

        # 4. Output Results
        output = OutputSchema(
            result="success",
            metadata={"count": len(results)},
        )
        # We need to add the actual results to the output. 
        # The OutputSchema in schema.py was defined as:
        # result: str, metadata: Dict, error: Optional[str]
        # It didn't have a 'data' field. Let's check schema.py again or just add it to metadata?
        # Better to have a 'data' field. I'll add it to metadata for now to strictly follow schema.py 
        # or I should have updated schema.py. 
        # Let's put it in metadata for now to be safe with the existing file I just wrote.
        
        output.metadata["results"] = results
        
        print(output.to_json())

    except Exception as e:
        # Catch-all for unexpected errors
        # In a secure kernel, we might not want to expose stack traces, 
        # but for debugging this reference implementation, it's useful.
        error_out(f"Internal Kernel Error: {str(e)}")

def error_out(message: str):
    """
    Helper to print error JSON.
    """
    output = OutputSchema(
        result="error",
        metadata={},
        error=message
    )
    print(output.to_json())

if __name__ == "__main__":
    main()
