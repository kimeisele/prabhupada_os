import sqlite3
import json
import sys
import argparse
import os

# Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), 'verses.db')

def initialize_db():
    """Initialize the SQLite database with a dummy verse if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT UNIQUE,
            sanskrit TEXT,
            translation TEXT,
            purport TEXT
        )
    ''')
    
    # Seed with dummy verse if empty
    cursor.execute('SELECT count(*) FROM verses')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO verses (reference, sanskrit, translation, purport)
            VALUES (?, ?, ?, ?)
        ''', (
            'BG 2.13',
            'dehino ’smin yathā dehe kaumāraṁ yauvanaṁ jarā\ntathā dehāntara-prāptir dhīras tatra na muhyati',
            'As the embodied soul continuously passes, in this body, from boyhood to youth to old age, the soul similarly passes into another body at death. A sober person is not bewildered by such a change.',
            'Since every living entity is an individual soul, each is changing his body every moment, manifesting sometimes as a child, sometimes as a youth, and sometimes as an old man...'
        ))
        conn.commit()
    
    conn.close()

def search(query):
    """Search the database for verses matching the query."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Simple LIKE search for now
    search_term = f'%{query}%'
    cursor.execute('''
        SELECT reference, sanskrit, translation 
        FROM verses 
        WHERE reference LIKE ? OR translation LIKE ? OR sanskrit LIKE ?
    ''', (search_term, search_term, search_term))
    
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    
    conn.close()
    return results

def get_random():
    """Retrieve a random verse from the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT reference, sanskrit, translation, purport 
        FROM verses 
        ORDER BY RANDOM() 
        LIMIT 1
    ''')
    
    row = cursor.fetchone()
    if row:
        result = [dict(row)]
    else:
        result = []
        
    conn.close()
    return result

def main():
    # Ensure DB exists
    initialize_db()
    
    parser = argparse.ArgumentParser(description="PrabhupadaOS Kernel Bridge")
    parser.add_argument("query", nargs="?", help="Search query for the verse database")
    parser.add_argument("--random", action="store_true", help="Get a random verse")
    
    args = parser.parse_args()
    
    try:
        if args.random:
            results = get_random()
        elif args.query:
            results = search(args.query)
        else:
            # No query and no random flag
            print(json.dumps({"status": "error", "message": "No query provided. Use 'query' or --random."}))
            return

        output = {
            "status": "success",
            "count": len(results),
            "data": results
        }
    except Exception as e:
        output = {
            "status": "error",
            "message": str(e)
        }
        
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
