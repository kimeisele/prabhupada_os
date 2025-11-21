from .core import PrabhupadaCore
from .intelligence import IntelligenceProvider
from .providers.dummy import DummyProvider
from typing import Optional, Dict, Any
from dataclasses import dataclass

# Global State
_core: Optional[PrabhupadaCore] = None
_intelligence: Optional[IntelligenceProvider] = None

@dataclass
class Response:
    sruti: list
    smriti: str
    meta: dict

def _get_core() -> PrabhupadaCore:
    global _core
    if _core is None:
        _core = PrabhupadaCore()
    return _core

def _get_intelligence() -> IntelligenceProvider:
    global _intelligence
    if _intelligence is None:
        _intelligence = DummyProvider()
    return _intelligence

def configure(db_path: Optional[str] = None, intelligence: Optional[IntelligenceProvider] = None):
    """
    Configure the Prabhupada OS.
    """
    global _core, _intelligence
    if db_path:
        _core = PrabhupadaCore(db_path)
    if intelligence:
        _intelligence = intelligence

def ask(query: str) -> Response:
    """
    The Main API.
    Ask a question to the Cyborg Sage.
    """
    core = _get_core()
    intel = _get_intelligence()
    
    # 1. Sruti (Retrieval)
    verses = core.search(query)
    
    # 2. Smriti (Synthesis)
    synthesis = intel.synthesize(query, verses)
    
    return Response(
        sruti=verses,
        smriti=synthesis,
        meta={"query": query, "provider": intel.__class__.__name__}
    )

def get_verse(chapter: int, verse: str) -> Optional[Dict]:
    """
    Get a specific verse.
    """
    return _get_core().get_verse(chapter, verse)
