"""
Simple CLI Chatbot - TIER 4 Demo
Tests the provider-agnostic architecture with SQLite FTS.
"""
import sys
import os

# Add prabhupada_os parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
os_dir = os.path.dirname(os.path.dirname(current_dir)) # prabhupada_os
parent_dir = os.path.dirname(os_dir) # parent of prabhupada_os
sys.path.insert(0, parent_dir)

from prabhupada_os.steward.core.router import QueryRouter
from prabhupada_os.steward.providers.sqlite_fts import SQLiteFTSProvider

def main():
    print("🕉️  PrabhupadaOS Chatbot (TIER 4 - SQLite FTS)")
    print("=" * 60)
    print()
    
    # Initialize router
    router = QueryRouter()
    
    # Register SQLite FTS provider
    sqlite_provider = SQLiteFTSProvider()
    router.register_provider(sqlite_provider)
    
    # Show status
    status = router.get_status()
    print(f"Providers available: {status['available_providers']}/{status['total_providers']}")
    for p in status['providers']:
        status_icon = "✅" if p['available'] else "❌"
        print(f"  {status_icon} TIER {p['tier']}: {p['name']}")
    print()
    print("Ask a question about the Bhagavad-gita (or 'quit' to exit)")
    print("-" * 60)
    print()
    
    # Chat loop
    while True:
        try:
            question = input("You: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n🙏 Hare Krishna!")
                break
            
            # Query the router
            response = router.query(question)
            
            print(f"\n{response.provider} (Confidence: {response.confidence:.0%}):")
            print(response.answer)
            print()
            
        except KeyboardInterrupt:
            print("\n\n🙏 Hare Krishna!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")

if __name__ == "__main__":
    main()
