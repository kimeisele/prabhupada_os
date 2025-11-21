import sqlite3
import json
import os

class PrabhupadaKernel:
    """
    The deterministic kernel of PrabhupadaOS.
    Implements the "No Speculation" protocol.
    """
    
    def __init__(self, db_path):
        self.db_path = db_path
        
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
        
    def search(self, query, limit=5):
        """
        Tier 1: SRUTI Retrieval.
        Searches the immutable database.
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Simple keyword search for MVP
        # In production, this would be vector search + keyword hybrid
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
                # Truncate purport for the preview, but full text is available
                "purport_snippet": row['purport'][:200] + "..." if row['purport'] else "",
                "source": "vedabase.db"
            })
            
        conn.close()
        return results

    def query(self, user_query):
        """
        The Main Interface.
        Returns the JSON-First response structure.
        """
        # 1. Retrieve SRUTI (The Truth)
        sruti_results = self.search(user_query)
        
        # 2. Synthesize SMRITI (The Interface)
        # In a real app, this would call an LLM with the sruti_results
        # For this kernel, we return a placeholder or a simple heuristic
        
        if not sruti_results:
            smriti_synthesis = "I could not find any verses matching your query in the current database."
        else:
            smriti_synthesis = f"I found {len(sruti_results)} verses related to '{user_query}'. The Bhagavad-gita addresses this directly."
            
        return {
            "meta": {
                "query": user_query,
                "protocol": "PrabhupadaOS v1.0",
                "status": "success"
            },
            "sruti": sruti_results,
            "smriti": {
                "synthesis": smriti_synthesis,
                "note": "AI synthesis is a servant of the Sruti data above."
            }
        }

# Demo usage
if __name__ == "__main__":
    # Path to DB
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, 'store', 'vedabase.db')
    
    kernel = PrabhupadaKernel(db_path)
    
    # Test Query
    q = "intelligence devotion"
    print(f"🔍 Querying: '{q}'...\n")
    
    response = kernel.query(q)
    
    print(json.dumps(response, indent=2))
