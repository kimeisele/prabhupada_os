import os
import yaml
import sqlite3
import re

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "cortex", "knowledge")
DB_PATH = os.path.join(BASE_DIR, "vedabase.db")

def get_all_verse_ids():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT book_code, chapter, verse FROM verses")
    # Store as "BG 1.1" format
    verses = set()
    for row in cursor.fetchall():
        book, chap, verse = row
        verses.add(f"{book} {chap}.{verse}")
    conn.close()
    return verses

def extract_refs_from_yaml(filepath):
    refs = []
    with open(filepath, 'r') as f:
        try:
            data = yaml.safe_load(f)
            # Recursively find 'key_verses' or any list of strings looking like "BG X.Y"
            # For now, let's just scan the raw text or traverse the dict?
            # Traversing is safer.
            
            def traverse(obj):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if k == "key_verses" and isinstance(v, list):
                            refs.extend(v)
                        else:
                            traverse(v)
                elif isinstance(obj, list):
                    for item in obj:
                        traverse(item)
            
            traverse(data)
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
    return refs

def verify_refs():
    print("=== YAML REFERENCE VERIFICATION ===")
    
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    valid_verses = get_all_verse_ids()
    print(f"Loaded {len(valid_verses)} valid verses from DB.")
    
    broken_links = 0
    
    for root, dirs, files in os.walk(KNOWLEDGE_DIR):
        for file in files:
            if file.endswith(".yaml") or file.endswith(".yml"):
                filepath = os.path.join(root, file)
                refs = extract_refs_from_yaml(filepath)
                
                file_broken = 0
                for ref in refs:
                    # Normalize ref if needed (e.g. "BG 2.12" -> "BG 2.12")
                    # Our DB has "BG 2.12".
                    
                    # Handle ranges in YAML? e.g. "BG 2.12-13"
                    # If YAML has range, we should check if individual verses exist?
                    # Or if the range string exists in DB (if we stored ranges)?
                    # We expanded ranges in DB to individual verses.
                    # So "BG 2.12-13" in YAML might not match "BG 2.12" in DB directly.
                    
                    # Logic: If ref is a range, check if all parts exist.
                    
                    parts = ref.split()
                    if len(parts) >= 2:
                        book = parts[0]
                        cv = parts[1]
                        if "-" in cv:
                            # Range
                            try:
                                chap, v_range = cv.split(".")
                                start, end = map(int, v_range.split("-"))
                                for i in range(start, end + 1):
                                    sub_ref = f"{book} {chap}.{i}"
                                    if sub_ref not in valid_verses:
                                        print(f"[BROKEN] {file}: {ref} (Missing {sub_ref})")
                                        file_broken += 1
                                        broken_links += 1
                            except:
                                print(f"[WARN] Could not parse range: {ref}")
                        else:
                            # Single
                            if ref not in valid_verses:
                                print(f"[BROKEN] {file}: {ref}")
                                file_broken += 1
                                broken_links += 1
    
    if broken_links == 0:
        print("\nSUCCESS: All YAML references are valid.")
    else:
        print(f"\nFAILURE: Found {broken_links} broken links.")

if __name__ == "__main__":
    verify_refs()
