import sys
import os
import subprocess
import json
import shutil
import textwrap
import random

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KERNEL_BRIDGE = os.path.join(BASE_DIR, "kernel", "bridge.py")
GRAPH_LOADER = os.path.join(BASE_DIR, "runtime", "graph_loader.py")

# Add runtime to path to import graph_loader
sys.path.append(os.path.join(BASE_DIR, "runtime"))
try:
    import graph_loader
except ImportError:
    graph_loader = None

# ANSI Colors
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"

# 1. Dynamic Imports (Graceful Degradation)
MODE = "KEYWORD"
try:
    import sentence_transformers
    MODE = "SEMANTIC"
except ImportError:
    MODE = "KEYWORD"

# Load Knowledge Graph
KNOWLEDGE_CONTEXT = {}
if graph_loader:
    try:
        KNOWLEDGE_CONTEXT = graph_loader.build_knowledge_context()
    except Exception as e:
        print(f"{YELLOW}Warning: Could not load Knowledge Graph: {e}{RESET}")

def print_banner():
    print(f"{CYAN}")
    print("╔════════════════════════════════════════════════════╗")
    print("║               PRABHUPADA OS v1.1                   ║")
    print("║         The Intelligence Container                 ║")
    print("╚════════════════════════════════════════════════════╝")
    print(f"{RESET}")
    print(f"Mode: {YELLOW}{MODE}{RESET}")
    if KNOWLEDGE_CONTEXT:
        print(f"Knowledge: {GREEN}Active (7 Dimensions){RESET}")
    print("Type 'help', 'exit', 'random', or any search query.\n")

def call_kernel(args):
    """Calls the Kernel bridge via subprocess."""
    cmd = [sys.executable, KERNEL_BRIDGE] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Kernel Error: {e.stderr}"}
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON from Kernel"}

def format_verse(verse):
    """Formats a single verse for display."""
    width = shutil.get_terminal_size().columns - 4
    
    print(f"\n{BOLD}{GREEN}>>> {verse.get('reference', 'Unknown Source')}{RESET}")
    
    sanskrit = verse.get('sanskrit', '').strip()
    if sanskrit:
        print(f"{GREEN}{textwrap.indent(sanskrit, '    ')}{RESET}\n")
        
    translation = verse.get('translation', '').strip()
    if translation:
        wrapped_trans = textwrap.fill(translation, width=width)
        print(f"{textwrap.indent(wrapped_trans, '    ')}\n")

def detect_intent(query):
    """
    Simple keyword matching against Shastra Map topics.
    Returns a list of suggested chapters.
    """
    suggestions = []
    if not KNOWLEDGE_CONTEXT:
        return suggestions
        
    topics = KNOWLEDGE_CONTEXT.get("shastra_map", {}).get("topics", [])
    query_lower = query.lower()
    
    for topic in topics:
        # Check if any word in topic name matches query
        # This is very naive, but fits "Offline/No-Dep" constraint.
        # Better: Check intersection of keywords.
        topic_keywords = set(topic["name"].lower().replace("/", " ").split())
        query_keywords = set(query_lower.split())
        
        if topic_keywords.intersection(query_keywords):
            suggestions.append(topic)
            
    return suggestions

def handle_search(query):
    # 1. Intent Routing
    suggestions = detect_intent(query)
    if suggestions:
        print(f"{MAGENTA}Context Detected:{RESET}")
        for s in suggestions:
            print(f"  • {BOLD}{s['name']}{RESET} -> {CYAN}Chapter {s['chapter']}{RESET} ({s['reason']})")
        print("")
        
    # 2. Search Execution
    if MODE == "SEMANTIC":
        print(f"{YELLOW}[System] Semantic Index building not yet implemented. Falling back to Keyword search.{RESET}")
    
    # Simple keyword cleaning
    stopwords = {'the', 'is', 'what', 'how', 'to', 'a', 'an', 'in', 'on', 'of', 'for', 'are'}
    keywords = [w for w in query.split() if w.lower() not in stopwords]
    cleaned_query = " ".join(keywords)
    
    if not cleaned_query:
        cleaned_query = query 
        
    print(f"{CYAN}Searching for: '{cleaned_query}'...{RESET}")
    
    response = call_kernel([cleaned_query])
    
    if response.get("status") == "success":
        data = response.get("data", [])
        count = response.get("count", 0)
        
        if count == 0:
            print(f"{YELLOW}No results found.{RESET}")
        else:
            print(f"{CYAN}Found {count} references.{RESET}")
            # Show top 3 results
            for verse in data[:3]:
                format_verse(verse)
            if count > 3:
                print(f"{YELLOW}... and {count - 3} more.{RESET}")
    else:
        print(f"{YELLOW}Error: {response.get('message')}{RESET}")

def handle_random():
    print(f"{CYAN}Consulting the Oracle...{RESET}")
    response = call_kernel(["--random"])
    
    if response.get("status") == "success":
        data = response.get("data", [])
        if data:
            format_verse(data[0])
        else:
            print(f"{YELLOW}The Oracle is silent (Database empty?).{RESET}")
    else:
        print(f"{YELLOW}Error: {response.get('message')}{RESET}")

def main():
    print_banner()
    
    while True:
        try:
            user_input = input(f"{BOLD}> {RESET}").strip()
            
            if not user_input:
                continue
                
            command = user_input.lower()
            
            if command in ['exit', 'quit', 'q']:
                print("Hare Krishna.")
                break
            elif command == 'help':
                print("\nCommands:")
                print("  help          - Show this message")
                print("  exit, quit    - Exit the shell")
                print("  random, quote - Get a random verse")
                print("  <text>        - Search for verses containing <text>")
                print("")
            elif command in ['random', 'quote', 'give me wisdom']:
                handle_random()
            else:
                handle_search(user_input)
                
        except KeyboardInterrupt:
            print("\nHare Krishna.")
            break
        except EOFError:
            print("\nHare Krishna.")
            break
        except Exception as e:
            print(f"\n{YELLOW}Shell Error: {e}{RESET}")

if __name__ == "__main__":
    main()
