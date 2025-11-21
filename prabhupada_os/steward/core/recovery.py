"""
Recovery Strategies - The Self-Correction Engine

This module implements error recovery and self-correction strategies
for the STEWARD agent. It handles failures gracefully with fallback
mechanisms and intelligent retry logic.

Recovery Strategies:
1. Low Similarity Handling: Fallback to keyword search
2. Empty Results: Query expansion and broadening
3. Validation Failures: Retry with stricter prompts
4. System Errors: Exponential backoff and escalation
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class RecoveryActionType(Enum):
    """Types of recovery actions"""
    RETRY = "retry"
    FALLBACK = "fallback"
    ESCALATE = "escalate"
    MODIFY_QUERY = "modify_query"
    SKIP = "skip"


@dataclass
class RecoveryAction:
    """A recovery action to take"""
    type: RecoveryActionType
    strategy: str
    params: Dict
    reason: str
    
    def __repr__(self):
        return f"RecoveryAction({self.type.value}: {self.strategy})"


class RecoveryStrategies:
    """
    Implements fallback and retry logic for failed operations.
    
    This is the "Self-Correction Engine" that makes STEWARD
    robust and autonomous.
    """
    
    def __init__(self, max_retries: int = 3):
        """
        Initialize recovery strategies.
        
        Args:
            max_retries: Maximum number of retry attempts
        """
        self.max_retries = max_retries
        self.retry_counts = {}  # Track retries per job
    
    def handle_low_similarity(
        self, 
        query: str, 
        results: List[Dict],
        threshold: float = 0.5
    ) -> RecoveryAction:
        """
        Handle cases where semantic search returns low similarity scores.
        
        Strategy:
        1. Try keyword search as fallback
        2. Expand query with synonyms
        3. Request clarification from Director
        
        Args:
            query: Original query
            results: Search results with low similarity
            threshold: Minimum acceptable similarity
            
        Returns:
            RecoveryAction to take
        """
        if not results:
            return self.handle_empty_results(query)
        
        # Check average similarity
        avg_similarity = sum(r.get('similarity', 0) for r in results) / len(results)
        
        if avg_similarity < threshold:
            # Strategy 1: Fallback to keyword search
            return RecoveryAction(
                type=RecoveryActionType.FALLBACK,
                strategy="keyword_search",
                params={"query": query},
                reason=f"Semantic search similarity too low: {avg_similarity:.2f}"
            )
        
        # Results are marginal, try query expansion
        return RecoveryAction(
            type=RecoveryActionType.MODIFY_QUERY,
            strategy="expand_query",
            params={"original_query": query},
            reason="Marginal results, attempting query expansion"
        )
    
    def handle_empty_results(self, query: str) -> RecoveryAction:
        """
        Handle cases where no results are found.
        
        Strategy:
        1. Broaden search terms
        2. Try related concepts
        3. Inform Director of knowledge gap
        
        Args:
            query: Original query
            
        Returns:
            RecoveryAction to take
        """
        # Try broadening the query
        return RecoveryAction(
            type=RecoveryActionType.MODIFY_QUERY,
            strategy="broaden_query",
            params={
                "original_query": query,
                "modifications": ["remove_specific_terms", "use_root_concepts"]
            },
            reason="No results found, broadening search"
        )
    
    def handle_validation_failure(
        self, 
        validation_result: Any,
        job_id: str = None
    ) -> RecoveryAction:
        """
        Handle cases where synthesis fails validation.
        
        Strategy:
        1. Retry with stricter prompt (if retries available)
        2. Use different verses
        3. Flag for human review
        
        Args:
            validation_result: The failed validation result
            job_id: Optional job ID for tracking retries
            
        Returns:
            RecoveryAction to take
        """
        # Check retry count
        if job_id:
            retry_count = self.retry_counts.get(job_id, 0)
        else:
            retry_count = 0
        
        if retry_count < self.max_retries:
            # Strategy 1: Retry with stricter prompt
            if job_id:
                self.retry_counts[job_id] = retry_count + 1
            
            return RecoveryAction(
                type=RecoveryActionType.RETRY,
                strategy="strict_validation",
                params={
                    "strict_mode": True,
                    "retry_attempt": retry_count + 1
                },
                reason=f"Validation failed (attempt {retry_count + 1}/{self.max_retries})"
            )
        else:
            # Max retries reached, escalate to human
            return RecoveryAction(
                type=RecoveryActionType.ESCALATE,
                strategy="human_review",
                params={
                    "validation_failures": getattr(validation_result, 'failures', []),
                    "retry_count": retry_count
                },
                reason="Max retries reached, requires human review"
            )
    
    def handle_system_error(
        self, 
        error: Exception,
        job_id: str = None,
        context: Dict = None
    ) -> RecoveryAction:
        """
        Handle system-level errors.
        
        Strategy:
        1. Exponential backoff retry
        2. Skip non-critical steps
        3. Escalate critical failures
        
        Args:
            error: The exception that occurred
            job_id: Optional job ID
            context: Optional error context
            
        Returns:
            RecoveryAction to take
        """
        error_type = type(error).__name__
        
        # Determine if error is recoverable
        recoverable_errors = [
            'TimeoutError',
            'ConnectionError',
            'TemporaryFailure'
        ]
        
        if error_type in recoverable_errors:
            # Retry with exponential backoff
            retry_count = self.retry_counts.get(job_id, 0) if job_id else 0
            
            if retry_count < self.max_retries:
                backoff_seconds = 2 ** retry_count  # 2, 4, 8 seconds
                
                if job_id:
                    self.retry_counts[job_id] = retry_count + 1
                
                return RecoveryAction(
                    type=RecoveryActionType.RETRY,
                    strategy="exponential_backoff",
                    params={
                        "wait_seconds": backoff_seconds,
                        "retry_attempt": retry_count + 1
                    },
                    reason=f"Recoverable error: {error_type}"
                )
        
        # Non-recoverable or max retries reached
        return RecoveryAction(
            type=RecoveryActionType.ESCALATE,
            strategy="critical_failure",
            params={
                "error_type": error_type,
                "error_message": str(error),
                "context": context or {}
            },
            reason=f"Critical system error: {error_type}"
        )
    
    def expand_query(self, query: str) -> str:
        """
        Expand a query with related terms.
        
        Simple implementation: add common related concepts.
        
        Args:
            query: Original query
            
        Returns:
            Expanded query
        """
        # Concept mapping for common theological terms
        expansions = {
            'soul': 'soul atma self consciousness',
            'karma': 'karma action work duty',
            'dharma': 'dharma duty righteousness religion',
            'yoga': 'yoga meditation union discipline',
            'krishna': 'krishna supreme lord bhagavan',
            'devotion': 'devotion bhakti service love'
        }
        
        query_lower = query.lower()
        
        for term, expansion in expansions.items():
            if term in query_lower:
                return expansion
        
        # No expansion found, return original
        return query
    
    def broaden_query(self, query: str) -> str:
        """
        Broaden a query by removing specific terms.
        
        Args:
            query: Original query
            
        Returns:
            Broadened query
        """
        # Remove question words and specific modifiers
        remove_words = ['what', 'how', 'why', 'when', 'where', 'specific', 'exactly']
        
        words = query.lower().split()
        filtered = [w for w in words if w not in remove_words]
        
        return ' '.join(filtered) if filtered else query
    
    def reset_retries(self, job_id: str):
        """Reset retry count for a job"""
        if job_id in self.retry_counts:
            del self.retry_counts[job_id]


# CLI for testing recovery strategies
if __name__ == "__main__":
    recovery = RecoveryStrategies(max_retries=3)
    
    print("🔧 Recovery Strategies Test")
    print("=" * 60)
    
    # Test 1: Low similarity
    print("\n1. Testing low similarity handling:")
    results = [{'similarity': 0.3}, {'similarity': 0.4}]
    action = recovery.handle_low_similarity("test query", results)
    print(f"   Action: {action}")
    
    # Test 2: Empty results
    print("\n2. Testing empty results handling:")
    action = recovery.handle_empty_results("obscure query")
    print(f"   Action: {action}")
    
    # Test 3: Validation failure with retries
    print("\n3. Testing validation failure (with retries):")
    for i in range(4):
        action = recovery.handle_validation_failure(None, job_id="test_job")
        print(f"   Attempt {i+1}: {action}")
    
    # Test 4: Query expansion
    print("\n4. Testing query expansion:")
    expanded = recovery.expand_query("What is the soul?")
    print(f"   Original: 'What is the soul?'")
    print(f"   Expanded: '{expanded}'")
    
    print("\n✅ Recovery strategies test complete")
