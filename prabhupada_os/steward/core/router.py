"""
Query Router - The Brain
Detects available providers and routes queries intelligently.
"""
from typing import List, Optional
from .provider import Provider, Response

class QueryRouter:
    """
    Central routing system for chatbot queries.
    
    Responsibilities:
    1. Detect which providers are available
    2. Select best provider based on tier
    3. Route query to selected provider
    4. Handle fallback if provider fails
    """
    
    def __init__(self):
        self.providers: List[Provider] = []
    
    def register_provider(self, provider: Provider):
        """Register a provider with the router"""
        self.providers.append(provider)
        # Sort by tier (lower tier = better)
        self.providers.sort(key=lambda p: p.get_tier())
    
    def get_available_providers(self) -> List[Provider]:
        """Get list of currently available providers"""
        return [p for p in self.providers if p.is_available()]
    
    def get_best_provider(self) -> Optional[Provider]:
        """Get the best available provider (lowest tier number)"""
        available = self.get_available_providers()
        return available[0] if available else None
    
    def query(self, question: str, max_results: int = 5) -> Response:
        """
        Route query to best available provider.
        
        Falls back to next tier if current provider fails.
        """
        available = self.get_available_providers()
        
        if not available:
            return Response(
                answer="No providers available. Please check your configuration.",
                citations=[],
                provider="None",
                confidence=0.0
            )
        
        # Try each provider in order (best to worst)
        last_error = None
        for provider in available:
            try:
                print(f"[Router] Using {provider.get_name()} (TIER {provider.get_tier()})")
                response = provider.query(question, max_results)
                return response
            except Exception as e:
                print(f"[Router] {provider.get_name()} failed: {e}")
                last_error = e
                continue
        
        # All providers failed
        return Response(
            answer=f"All providers failed. Last error: {last_error}",
            citations=[],
            provider="None",
            confidence=0.0
        )
    
    def get_status(self) -> dict:
        """Get status of all registered providers"""
        return {
            'total_providers': len(self.providers),
            'available_providers': len(self.get_available_providers()),
            'providers': [
                {
                    'name': p.get_name(),
                    'tier': p.get_tier(),
                    'available': p.is_available()
                }
                for p in self.providers
            ]
        }
