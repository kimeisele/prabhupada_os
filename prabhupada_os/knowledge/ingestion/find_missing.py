import sqlite3
import os

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "vedabase.db")

# Standard Gita Structure (Chapter: Verse Count)
EXPECTED_COUNTS = {
    1: 46, # Some editions say 47, 1972 usually 46
    2: 72,
    3: 43,
    4: 42,
    5: 29,
    6: 47,
    7: 30,
    8: 28,
    9: 34,
    10: 42,
    11: 55,
    12: 20,
    13: 35, 
    14: 27,
    15: 20,
    16: 24,
    17: 28,
    18: 78
}

def find_missing():
    # Database setup
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # prabhupada_os/knowledge
    db_path = os.path.join(base_dir, 'store', 'vedabase.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=== GITA GAP ANALYSIS ===")
    
    total_missing_ids = []

    for chapter_num, expected_count in EXPECTED_COUNTS.items():
        cursor.execute(
            "SELECT verse FROM verses WHERE book_code='BG' AND chapter=?", 
            (chapter_num,)
        )
        # Normalize verse numbers (handle "1", "1-2", etc.)
        existing_verses = set()
        raw_verses = [row[0] for row in cursor.fetchall()]
        
        for v in raw_verses:
            parts = v.split('-')
            if len(parts) == 1:
                if parts[0].isdigit():
                    existing_verses.add(int(parts[0]))
            elif len(parts) == 2:
                if parts[0].isdigit() and parts[1].isdigit():
                    start = int(parts[0])
                    end = int(parts[1])
                    for i in range(start, end + 1):
                        existing_verses.add(i)

        missing_in_chapter = []
        for i in range(1, expected_count + 1):
            if i not in existing_verses:
                missing_in_chapter.append(f"BG {chapter_num}.{i}")
                total_missing_ids.append(f"BG {chapter_num}.{i}")
        
        if missing_in_chapter:
            print(f"Chapter {chapter_num}: Missing {len(missing_in_chapter)} verses")
            # print(f"  {missing_in_chapter}")

    print(f"\nTotal Missing Verses: {len(total_missing_ids)}")
    if total_missing_ids:
        print("Sample Missing IDs:")
        for i in total_missing_ids[:10]:
            print(f"  - {i}")
            
    conn.close()

if __name__ == "__main__":
    find_missing()
