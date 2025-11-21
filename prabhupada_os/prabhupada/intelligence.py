from abc import ABC, abstractmethod
from typing import List, Dict

class IntelligenceProvider(ABC):
    """
    The Abstract Interface for Smriti (Intelligence).
    Any AI provider must implement this protocol.
    """
    
    @abstractmethod
    def synthesize(self, query: str, verses: List[Dict]) -> str:
        """
        Synthesize an answer based ONLY on the provided verses.
        """
        pass
