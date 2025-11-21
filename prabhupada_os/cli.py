import argparse
import json
import sys
import os

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import prabhupada
from prabhupada.core import PrabhupadaCore

def get_status():
    """
    Returns the system state (Observability).
    """
    try:
        # Check DB connection
        core = PrabhupadaCore()
        conn = core._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM verses")
        count = cursor.fetchone()[0]
        conn.close()
        
        return {
            "status": "online",
            "database": {
                "connected": True,
                "path": core.db_path,
                "verse_count": count,
                "integrity": "valid"
            },
            "kernel": {
                "version": "1.0.0",
                "mode": "library"
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e)
        }

def main():
    parser = argparse.ArgumentParser(description="PrabhupadaOS AI-Native CLI")
    parser.add_argument('--json', action='store_true', help="Output in JSON format (for AI operators)")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status Command
    status_parser = subparsers.add_parser('status', help='Get system health and state')
    status_parser.add_argument('--json', action='store_true', help="Output in JSON format")

    # Search Command
    search_parser = subparsers.add_parser('search', help='Semantic search for verses')
    search_parser.add_argument('query', type=str, help='The search query')
    search_parser.add_argument('--limit', type=int, default=5, help='Max results')
    search_parser.add_argument('--json', action='store_true', help="Output in JSON format")

    args = parser.parse_args()

    # Default to JSON if no command (Help)
    if not args.command:
        if args.json:
            print(json.dumps({
                "name": "prabhupada-cli",
                "commands": [
                    {"name": "status", "description": "Get system health"},
                    {"name": "search", "args": ["query", "limit"]}
                ]
            }, indent=2))
        else:
            parser.print_help()
        return

    # Handle Status
    if args.command == 'status':
        status = get_status()
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print(f"🟢 System Status: {status['status'].upper()}")
            print(f"📚 Database: {status['database']['verse_count']} verses loaded")
            print(f"📍 Path: {status['database']['path']}")

    # Handle Search
    elif args.command == 'search':
        try:
            # Use the Library Facade
            response = prabhupada.ask(args.query)
            
            if args.json:
                output = {
                    "success": True,
                    "meta": response.meta,
                    "data": {
                        "count": len(response.sruti),
                        "verses": response.sruti,
                        "synthesis": response.smriti
                    }
                }
                print(json.dumps(output, indent=2))
            else:
                print(f"🔍 Found {len(response.sruti)} verses for '{args.query}'\n")
                for v in response.sruti:
                    print(f"[{v['id']}] {v['translation'][:100]}...")
                print(f"\n🧠 Synthesis: {response.smriti}")
                
        except Exception as e:
            error_out = {
                "success": False,
                "error": {
                    "code": "EXECUTION_ERROR",
                    "message": str(e)
                }
            }
            if args.json:
                print(json.dumps(error_out, indent=2))
            else:
                print(f"❌ Error: {str(e)}")
                sys.exit(1)

if __name__ == "__main__":
    main()
