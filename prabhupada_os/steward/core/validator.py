"""
Smriti Validator - The Boundary Guardian

This module implements the core validation logic to ensure that AI-generated
synthesis (Smriti) accurately represents the source verses (Sruti).

The validator prevents the "Boundary Problem" - where the AI correctly cites
verses but misinterprets their meaning.

Three-Tier Validation:
1. Logical Consistency: Does the synthesis contradict any cited verse?
2. Citation Accuracy: Is each verse used in the correct context?
3. Doctrinal Alignment: Does the interpretation match established teachings?
"""

import os
import yaml
from typing import List, Dict, Optional
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer, util


@dataclass
class ValidationResult:
    """Result of Smriti validation"""
    passed: bool
    score: float
    failures: List[Dict]
    warnings: List[Dict]
    details: Dict
    
    def __repr__(self):
        status = "✅ PASSED" if self.passed else "❌ FAILED"
        return f"ValidationResult({status}, score={self.score:.2f}, failures={len(self.failures)})"


class SmritiValidator:
    """
    Validates AI-generated synthesis against source verses.
    
    This is the "Boundary Guardian" that prevents misinterpretation
    while allowing legitimate synthesis and explanation.
    """
    
    def __init__(self, rules_path: Optional[str] = None):
        """
        Initialize the validator.
        
        Args:
            rules_path: Path to validation rules YAML file
        """
        if rules_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            rules_path = os.path.join(
                os.path.dirname(current_dir), 
                'validation', 
                'rules.yaml'
            )
        
        self.rules_path = rules_path
        self.rules = self._load_rules()
        
        # Load semantic model for consistency checking
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def _load_rules(self) -> Dict:
        """Load validation rules from YAML"""
        if not os.path.exists(self.rules_path):
            # Return default rules if file doesn't exist
            return self._get_default_rules()
            
        with open(self.rules_path) as f:
            return yaml.safe_load(f)
    
    def _get_default_rules(self) -> Dict:
        """Default validation rules"""
        return {
            'rules': [
                {
                    'id': 'no_contradiction',
                    'type': 'logical_consistency',
                    'threshold': 0.7,
                    'description': 'Synthesis must not contradict any cited verse'
                },
                {
                    'id': 'citation_relevance',
                    'type': 'citation_accuracy',
                    'threshold': 0.6,
                    'description': 'Each cited verse must support the claim'
                },
                {
                    'id': 'doctrinal_match',
                    'type': 'doctrinal_alignment',
                    'threshold': 0.5,
                    'description': 'Synthesis must align with established teachings'
                }
            ]
        }
    
    def validate_synthesis(
        self, 
        smriti: str, 
        sruti: List[Dict],
        strict: bool = False
    ) -> ValidationResult:
        """
        Validate AI synthesis against source verses.
        
        Args:
            smriti: The AI-generated synthesis/interpretation
            sruti: List of source verses (each with 'id', 'translation', etc.)
            strict: If True, use stricter thresholds
            
        Returns:
            ValidationResult with pass/fail and detailed feedback
        """
        failures = []
        warnings = []
        scores = {}
        
        # 1. Logical Consistency Check
        consistency_result = self.check_logical_consistency(smriti, sruti)
        scores['logical_consistency'] = consistency_result['score']
        
        if consistency_result['contradictions']:
            for contradiction in consistency_result['contradictions']:
                failures.append({
                    'rule': 'no_contradiction',
                    'type': 'logical_consistency',
                    'severity': 'critical',
                    'message': f"Synthesis contradicts verse {contradiction['verse_id']}",
                    'details': contradiction
                })
        
        # 2. Citation Accuracy Check
        citation_result = self.verify_citation_accuracy(smriti, sruti)
        scores['citation_accuracy'] = citation_result['score']
        
        for verse in citation_result['weak_citations']:
            if verse['relevance'] < 0.4:
                failures.append({
                    'rule': 'citation_relevance',
                    'type': 'citation_accuracy',
                    'severity': 'high',
                    'message': f"Verse {verse['verse_id']} poorly supports the synthesis",
                    'details': verse
                })
            else:
                warnings.append({
                    'rule': 'citation_relevance',
                    'type': 'citation_accuracy',
                    'severity': 'medium',
                    'message': f"Verse {verse['verse_id']} weakly supports the synthesis",
                    'details': verse
                })
        
        # 3. Doctrinal Alignment Check
        doctrinal_result = self.assess_doctrinal_alignment(smriti, sruti)
        scores['doctrinal_alignment'] = doctrinal_result['score']
        
        if doctrinal_result['score'] < self._get_threshold('doctrinal_match', strict):
            warnings.append({
                'rule': 'doctrinal_match',
                'type': 'doctrinal_alignment',
                'severity': 'low',
                'message': 'Synthesis may deviate from established doctrinal patterns',
                'details': doctrinal_result
            })
        
        # Calculate overall score
        overall_score = sum(scores.values()) / len(scores)
        
        # Determine pass/fail
        passed = len(failures) == 0 and overall_score >= 0.6
        
        return ValidationResult(
            passed=passed,
            score=overall_score,
            failures=failures,
            warnings=warnings,
            details={
                'scores': scores,
                'consistency': consistency_result,
                'citation': citation_result,
                'doctrinal': doctrinal_result
            }
        )
    
    def check_logical_consistency(
        self, 
        synthesis: str, 
        verses: List[Dict]
    ) -> Dict:
        """
        Check if synthesis contradicts any cited verse.
        
        Uses semantic similarity to detect contradictions.
        A contradiction is when the synthesis makes a claim that is
        semantically opposite to what a verse states.
        
        Args:
            synthesis: The AI-generated text
            verses: Source verses
            
        Returns:
            Dict with score and list of contradictions
        """
        contradictions = []
        
        # Extract claims from synthesis (split into sentences)
        synthesis_sentences = [s.strip() for s in synthesis.split('.') if s.strip()]
        
        # Encode synthesis and verses
        synthesis_embeddings = self.model.encode(synthesis_sentences, convert_to_tensor=True)
        
        for verse in verses:
            verse_text = verse.get('translation', '')
            if not verse_text:
                continue
                
            verse_embedding = self.model.encode(verse_text, convert_to_tensor=True)
            
            # Check each synthesis sentence against the verse
            for i, sent_embedding in enumerate(synthesis_embeddings):
                similarity = util.cos_sim(sent_embedding, verse_embedding).item()
                
                # Very low similarity might indicate contradiction
                # (or just unrelated content, so we need to be careful)
                if similarity < 0.1 and len(synthesis_sentences[i].split()) > 5:
                    # Only flag if the sentence is substantial
                    contradictions.append({
                        'verse_id': verse['id'],
                        'verse_text': verse_text[:100] + '...',
                        'synthesis_claim': synthesis_sentences[i],
                        'similarity': similarity
                    })
        
        # Score: 1.0 if no contradictions, decreases with more contradictions
        score = max(0.0, 1.0 - (len(contradictions) * 0.2))
        
        return {
            'score': score,
            'contradictions': contradictions,
            'total_checked': len(verses)
        }
    
    def verify_citation_accuracy(
        self, 
        synthesis: str, 
        verses: List[Dict]
    ) -> Dict:
        """
        Verify that each cited verse actually supports the synthesis.
        
        Args:
            synthesis: The AI-generated text
            verses: Source verses
            
        Returns:
            Dict with score and list of weak citations
        """
        weak_citations = []
        relevance_scores = []
        
        # Encode the full synthesis
        synthesis_embedding = self.model.encode(synthesis, convert_to_tensor=True)
        
        for verse in verses:
            verse_text = verse.get('translation', '')
            if not verse_text:
                continue
            
            # Check how relevant this verse is to the synthesis
            verse_embedding = self.model.encode(verse_text, convert_to_tensor=True)
            relevance = util.cos_sim(synthesis_embedding, verse_embedding).item()
            
            relevance_scores.append(relevance)
            
            # Flag weak citations
            if relevance < 0.6:
                weak_citations.append({
                    'verse_id': verse['id'],
                    'verse_text': verse_text[:100] + '...',
                    'relevance': relevance
                })
        
        # Average relevance score
        avg_score = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
        
        return {
            'score': avg_score,
            'weak_citations': weak_citations,
            'average_relevance': avg_score,
            'total_verses': len(verses)
        }
    
    def assess_doctrinal_alignment(
        self, 
        synthesis: str, 
        verses: List[Dict]
    ) -> Dict:
        """
        Assess if synthesis aligns with established doctrinal patterns.
        
        This is a heuristic check based on:
        1. Use of established terminology
        2. Consistency with verse themes
        3. Appropriate tone and framing
        
        Args:
            synthesis: The AI-generated text
            verses: Source verses (for context)
            
        Returns:
            Dict with alignment score and details
        """
        # Doctrinal keywords that should appear in proper synthesis
        doctrinal_terms = [
            'krishna', 'arjuna', 'soul', 'karma', 'dharma', 'yoga',
            'devotion', 'supreme', 'eternal', 'transcendental', 'material',
            'spiritual', 'consciousness', 'lord', 'bhagavad-gita'
        ]
        
        synthesis_lower = synthesis.lower()
        
        # Count doctrinal term usage
        term_count = sum(1 for term in doctrinal_terms if term in synthesis_lower)
        term_score = min(1.0, term_count / 5)  # Expect at least 5 terms
        
        # Check if synthesis is appropriately reverent (not speculative)
        speculative_phrases = [
            'i think', 'i believe', 'probably', 'maybe', 'perhaps',
            'it seems', 'might be', 'could be'
        ]
        
        speculation_count = sum(1 for phrase in speculative_phrases if phrase in synthesis_lower)
        speculation_penalty = min(0.5, speculation_count * 0.1)
        
        # Final score
        alignment_score = max(0.0, term_score - speculation_penalty)
        
        return {
            'score': alignment_score,
            'doctrinal_terms_found': term_count,
            'speculation_detected': speculation_count > 0,
            'details': {
                'term_score': term_score,
                'speculation_penalty': speculation_penalty
            }
        }
    
    def _get_threshold(self, rule_id: str, strict: bool = False) -> float:
        """Get threshold for a specific rule"""
        for rule in self.rules.get('rules', []):
            if rule['id'] == rule_id:
                threshold = rule['threshold']
                return threshold * 1.2 if strict else threshold
        return 0.5  # Default threshold


# CLI for testing validator
if __name__ == "__main__":
    import sys
    
    # Example usage
    validator = SmritiValidator()
    
    # Test case: Good synthesis
    good_smriti = """
    The soul is eternal and indestructible. According to the Bhagavad-gita,
    the soul cannot be cut by weapons, burned by fire, or dried by wind.
    Krishna explains to Arjuna that the soul transmigrates from body to body,
    just as a person changes worn-out garments.
    """
    
    good_sruti = [
        {
            'id': 'BG 2.20',
            'translation': 'For the soul there is neither birth nor death at any time. He has not come into being, does not come into being, and will not come into being. He is unborn, eternal, ever-existing and primeval. He is not slain when the body is slain.'
        },
        {
            'id': 'BG 2.23',
            'translation': 'The soul can never be cut to pieces by any weapon, nor burned by fire, nor moistened by water, nor withered by the wind.'
        }
    ]
    
    print("Testing GOOD synthesis:")
    result = validator.validate_synthesis(good_smriti, good_sruti)
    print(result)
    print(f"\nScore breakdown: {result.details['scores']}")
    
    # Test case: Bad synthesis (misinterpretation)
    bad_smriti = """
    The soul is temporary and will eventually cease to exist.
    When the body dies, the soul also perishes completely.
    """
    
    print("\n" + "="*60)
    print("Testing BAD synthesis (contradiction):")
    result = validator.validate_synthesis(bad_smriti, good_sruti)
    print(result)
    print(f"\nFailures: {len(result.failures)}")
    for failure in result.failures:
        print(f"  - {failure['message']}")
