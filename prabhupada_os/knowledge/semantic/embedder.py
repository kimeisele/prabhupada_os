import os
import sys
import sqlite3
import pickle
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Add the prabhupada_os directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
prabhupada_os_dir = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.insert(0, prabhupada_os_dir)

from prabhupada.core import PrabhupadaCore

def generate_embeddings():
    print("🧠 Loading Semantic Model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("📚 Fetching Verses from Vedabase...")
    core = PrabhupadaCore()
    conn = core._get_connection()
    c = conn.cursor()
    c.execute("SELECT book_code, chapter, verse, translation, purport FROM verses")
    rows = c.fetchall()
    conn.close()
    
    print(f"✨ Found {len(rows)} verses. Generating embeddings...")
    
    verse_data = []
    texts = []
    
    for row in rows:
        verse_id = f"{row[0]} {row[1]}.{row[2]}"
        # Combine translation and purport for rich semantic context
        # We truncate purport to 1000 chars to keep it focused and fast
        purport_snippet = row[4][:1000] if row[4] else ""
        text = f"{row[3]} {purport_snippet}"
        
        verse_data.append({
            "id": verse_id,
            "translation": row[3],
            "purport_snippet": purport_snippet
        })
        texts.append(text)
        
    # Generate embeddings in batch
    embeddings = model.encode(texts, show_progress_bar=True)
    
    # Save to file
    output_path = os.path.join(os.path.dirname(core.db_path), 'vectors.pkl')
    
    print(f"💾 Saving {len(embeddings)} vectors to {output_path}...")
    
    with open(output_path, 'wb') as f:
        pickle.dump({
            "verse_data": verse_data,
            "embeddings": embeddings
        }, f)
        
    print("✅ Semantic Index Created!")

if __name__ == "__main__":
    generate_embeddings()
