import sqlite3
import os
from typing import List, Dict, Optional

class PrabhupadaCore:
    """
    The Immutable Kernel (Sruti).
    Responsible for retrieving raw verses from the Vedabase.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default to the internal store
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(current_dir, '../knowledge/store/vedabase.db')
        else:
            self.db_path = db_path
            
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
        
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Retrieve verses based on keyword search.
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        keywords = query.lower().split()
        conditions = []
        params = []
        
        for kw in keywords:
            conditions.append("(lower(translation) LIKE ? OR lower(purport) LIKE ?)")
            params.extend([f'%{kw}%', f'%{kw}%'])
            
        where_clause = " AND ".join(conditions)
        
        sql = f"""
            SELECT book_code, chapter, verse, sanskrit, translation, purport 
            FROM verses 
            WHERE {where_clause}
            LIMIT ?
        """
        params.append(limit)
        
        c.execute(sql, params)
        rows = c.fetchall()
        
        results = []
        for row in rows:
            results.append({
                "id": f"{row['book_code']} {row['chapter']}.{row['verse']}",
                "sanskrit": row['sanskrit'],
                "translation": row['translation'],
                "purport": row['purport'],
                "source": "vedabase.db"
            })
            
        conn.close()
        return results

    def get_verse(self, chapter: int, verse: str) -> Optional[Dict]:
        """
        Retrieve a specific verse by citation.
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("""
            SELECT book_code, chapter, verse, sanskrit, translation, purport 
            FROM verses 
            WHERE chapter = ? AND verse = ?
        """, (chapter, verse))
        
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                "id": f"{row['book_code']} {row['chapter']}.{row['verse']}",
                "sanskrit": row['sanskrit'],
                "translation": row['translation'],
                "purport": row['purport'],
                "source": "vedabase.db"
            }
        return None
