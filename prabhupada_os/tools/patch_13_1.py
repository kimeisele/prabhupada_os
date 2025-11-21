import sqlite3
import os
import hashlib

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "vedabase.db")

def compute_hash(sanskrit, translation, purport):
    """Compute SHA256 hash of the content to ensure immutability."""
    content = f"{sanskrit}|{translation}|{purport}"
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def patch_13_1():
    print("=== PATCHING BG 13.1 ===")
    
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Data for BG 13.1
    book_code = "BG"
    chapter = 13
    verse = "1"
    sanskrit = "arjuna uvāca\nprakṛtiṁ puruṣaṁ caiva kṣetraṁ kṣetra-jñam eva ca\netad veditum icchāmi jñānaṁ jñeyaṁ ca keśava"
    translation = "Arjuna said: O my dear Krsna, I wish to know about prakrti [nature], purusa [the enjoyer], and the field and the knower of the field, and of knowledge and the object of knowledge."
    purport = "" # No purport for this specific verse in some editions, or we leave empty if not provided.
    synonyms = "" # Not provided in prompt, leaving empty.

    content_hash = compute_hash(sanskrit, translation, purport)

    try:
        cursor.execute('''
            INSERT OR REPLACE INTO verses (book_code, chapter, verse, sanskrit, synonyms, translation, purport, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            book_code, 
            chapter, 
            verse, 
            sanskrit,
            synonyms,
            translation,
            purport,
            content_hash
        ))
        print("BG 13.1 Patched Successfully.")
    except sqlite3.IntegrityError as e:
        print(f"Error inserting BG 13.1: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    # Verify Total Count
    cursor.execute("SELECT COUNT(*) FROM verses WHERE book_code='BG'")
    count = cursor.fetchone()[0]
    print(f"Total Verses in DB: {count}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    patch_13_1()
