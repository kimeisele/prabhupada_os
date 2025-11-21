"""
Provider Interface - Abstract Base Class
All chatbot providers must implement this interface.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Citation:
    """Reference to a verse in the knowledge base"""
    book_code: str
    chapter: int
    verse: str
    text: str  # Relevant excerpt

@dataclass
class Response:
    """Standardized response from any provider"""
    answer: str
    citations: List[Citation]
    provider: str  # Which provider generated this
    confidence: float  # 0.0 to 1.0

class Provider(ABC):
    """
    Abstract base class for all chatbot providers.
    
    Each provider (SQLite FTS, Sentence Transformers, OpenAI, etc.)
    implements this interface, allowing the Query Router to treat
    them uniformly.
    """
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this provider is available.
        
        Returns:
            True if provider can be used, False otherwise
            
        Examples:
            - SQLite FTS: Always returns True
            - OpenAI: Returns True if API key is set
            - Sentence Transformers: Returns True if model is loaded
        """
        pass
    
    @abstractmethod
    def query(self, question: str, max_results: int = 5) -> Response:
        """
        Process a user question and return an answer.
        
        Args:
            question: User's question
            max_results: Maximum number of citations to include
            
        Returns:
            Response object with answer and citations
        """
        pass
    
    @abstractmethod
    def get_tier(self) -> int:
        """
        Return the tier level (1-4) of this provider.
        
        Returns:
            1: Claude MCP (best)
            2: OpenAI/Anthropic APIs
            3: Sentence Transformers (local)
            4: SQLite FTS (offline)
        """
        pass
    
    def get_name(self) -> str:
        """Return human-readable name of this provider"""
        return self.__class__.__name__
