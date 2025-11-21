import sys
import os
import json
import subprocess

# Path configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KERNEL_PATH = os.path.join(BASE_DIR, "kernel", "main.py")

def call_kernel(query: str) -> dict:
    """
    Calls the Kernel via subprocess (STDIN/STDOUT).
    This enforces the "Air Gap" / Process Boundary.
    """
    input_data = json.dumps({"query": query})
    
    process = subprocess.Popen(
        [sys.executable, KERNEL_PATH],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = process.communicate(input=input_data)
    
    if stderr:
        print(f"Kernel Stderr: {stderr}", file=sys.stderr)
        
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON from Kernel", "raw_output": stdout}

def main():
    print("PrabhupadaOS Runtime Loader")
    print("---------------------------")
    
    while True:
        try:
            query = input("Enter search query (or 'exit'): ")
            if query.lower() == 'exit':
                break
                
            response = call_kernel(query)
            print(json.dumps(response, indent=2))
            
        except KeyboardInterrupt:
            break
            
    print("\nShutting down.")

if __name__ == "__main__":
    main()
