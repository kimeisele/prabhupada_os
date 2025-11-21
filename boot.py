#!/usr/bin/env python3
import subprocess
import json
import sys
import os

def boot():
    """
    The One Final Boot Script.
    Entry point for AI Operators.
    """
    print("🤖 AI Operator Boot Sequence Initiated...")
    
    # Path to CLI
    cli_path = os.path.join(os.path.dirname(__file__), 'prabhupada_os', 'cli.py')
    
    try:
        # Run Status Check
        result = subprocess.run(
            [sys.executable, cli_path, 'status', '--json'],
            capture_output=True,
            text=True,
            check=True
        )
        
        status = json.loads(result.stdout)
        
        if status.get('status') == 'online':
            print("\n✅ SYSTEM ONLINE")
            print(json.dumps(status, indent=2))
            print("\nReady for commands. See AI_OPERATOR_MANUAL.md")
            sys.exit(0)
        else:
            print("\n❌ SYSTEM DEGRADED")
            print(json.dumps(status, indent=2))
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ BOOT FAILED: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    boot()
