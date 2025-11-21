"""
SQLite FTS Provider - TIER 4 (Offline, Always Available)
Uses SQLite Full-Text Search for keyword-based verse retrieval.
"""
import sqlite3
import os
from typing import List
# Import from steward.core.provider
# We are in prabhupada_os.steward.providers
from ..core.provider import Provider, Response, Citation

class SQLiteFTSProvider(Provider):
    """
    TIER 4: SQLite Full-Text Search Provider
    
    - Always available (no dependencies)
    - Works offline
    - Keyword-based search (not semantic)
    - Fast and lightweight
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Get path to prabhupada_os directory
            # self file is in prabhupada_os/steward/providers/sqlite_fts.py
            providers_dir = os.path.dirname(os.path.abspath(__file__))
            steward_dir = os.path.dirname(providers_dir)
            os_dir = os.path.dirname(steward_dir)
            db_path = os.path.join(os_dir, 'knowledge', 'store', 'vedabase.db')
        
        self.db_path = db_path
        self._ensure_fts_index()
    
    def _ensure_fts_index(self):
        """Create FTS5 virtual table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if FTS table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='verses_fts'
        """)
        
        if not cursor.fetchone():
            print("Creating FTS5 index...")
            # Create FTS table without content= parameter (standalone FTS table)
            cursor.execute("""
                CREATE VIRTUAL TABLE verses_fts USING fts5(
                    book_code, chapter, verse, 
                    sanskrit, translation, purport
                )
            """)
            
            # Populate FTS table from verses
            cursor.execute("""
                INSERT INTO verses_fts(book_code, chapter, verse, sanskrit, translation, purport)
                SELECT book_code, chapter, verse, 
                       COALESCE(sanskrit, ''), 
                       COALESCE(translation, ''), 
                       COALESCE(purport, '')
                FROM verses
            """)
            
            conn.commit()
            print("FTS5 index created!")
        
        conn.close()
    
    def is_available(self) -> bool:
        """SQLite FTS is always available"""
        return os.path.exists(self.db_path)
    
    def get_tier(self) -> int:
        """TIER 4 - Offline, keyword search"""
        return 4
    
    def query(self, question: str, max_results: int = 5) -> Response:
        """
        Search verses using keyword matching.
        
        Extracts keywords from question and searches translation + purport.
        """
        # Extract keywords (simple approach: remove common words)
        stop_words = {'what', 'does', 'say', 'about', 'the', 'is', 'in', 'a', 'an', 'and', 'or', 'but', 'how', 'why', 'when', 'where', 'who'}
        keywords = [w.lower() for w in question.split() if w.lower() not in stop_words]
        
        if not keywords:
            return Response(
                answer="Please provide a more specific question.",
                citations=[],
                provider=self.get_name(),
                confidence=0.0
            )
        
        # Build FTS query
        fts_query = ' OR '.join(keywords)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Search using FTS5
        cursor.execute(f"""
            SELECT v.book_code, v.chapter, v.verse, v.translation, v.purport
            FROM verses_fts fts
            JOIN verses v ON fts.book_code = v.book_code 
                          AND fts.chapter = v.chapter 
                          AND fts.verse = v.verse
            WHERE fts MATCH ?
            ORDER BY bm25(fts)
            LIMIT ?
        """, (fts_query, max_results))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return Response(
                answer=f"No verses found matching: {', '.join(keywords)}",
                citations=[],
                provider=self.get_name(),
                confidence=0.0
            )
        
        # Build citations
        citations = []
        for book_code, chapter, verse, translation, purport in results:
            citations.append(Citation(
                book_code=book_code,
                chapter=chapter,
                verse=verse,
                text=translation[:200] + "..." if len(translation) > 200 else translation
            ))
        
        # Build answer
        answer = f"Found {len(results)} relevant verse(s):\n\n"
        for i, (book_code, chapter, verse, translation, purport) in enumerate(results, 1):
            answer += f"{i}. **{book_code} {chapter}.{verse}**\n"
            answer += f"   {translation[:150]}...\n\n"
        
        return Response(
            answer=answer,
            citations=citations,
            provider=self.get_name(),
            confidence=min(len(results) / max_results, 1.0)
        )
