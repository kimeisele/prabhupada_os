import sqlite3
import os
import pickle
import numpy as np
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
            
        # Lazy load semantic index
        self._semantic_index = None
        self._semantic_model = None
            
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def _load_semantic_index(self):
        """Lazy load the semantic index"""
        if self._semantic_index is None:
            vectors_path = os.path.join(os.path.dirname(self.db_path), 'vectors.pkl')
            if os.path.exists(vectors_path):
                with open(vectors_path, 'rb') as f:
                    self._semantic_index = pickle.load(f)
        return self._semantic_index
    
    def _get_semantic_model(self):
        """Lazy load the sentence transformer model"""
        if self._semantic_model is None:
            from sentence_transformers import SentenceTransformer
            self._semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
        return self._semantic_model
        
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

    def semantic_search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Retrieve verses based on semantic similarity (concept-based).
        """
        index = self._load_semantic_index()
        if index is None:
            raise Exception("Semantic index not found. Run embedder.py first.")
        
        model = self._get_semantic_model()
        
        # Encode the query
        query_embedding = model.encode([query])[0]
        
        # Calculate cosine similarity
        embeddings = index['embeddings']
        similarities = np.dot(embeddings, query_embedding) / (
            np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get top results
        top_indices = np.argsort(similarities)[::-1][:limit]
        
        results = []
        for idx in top_indices:
            verse_data = index['verse_data'][idx]
            results.append({
                "id": verse_data['id'],
                "translation": verse_data['translation'],
                "purport": verse_data['purport_snippet'],
                "similarity": float(similarities[idx]),
                "source": "vedabase.db (semantic)"
            })
        
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
