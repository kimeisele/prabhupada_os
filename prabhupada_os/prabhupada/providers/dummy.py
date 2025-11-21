from ..intelligence import IntelligenceProvider
from typing import List, Dict

class DummyProvider(IntelligenceProvider):
    """
    The Default Offline Provider.
    Does not use AI. Just summarizes the search results.
    """
    
    def synthesize(self, query: str, verses: List[Dict]) -> str:
        count = len(verses)
        if count == 0:
            return "I could not find any verses matching your query in the current database."
        
        return f"I found {count} verses related to '{query}'. The Bhagavad-gita addresses this directly. Please read the verses below for the authoritative answer."
