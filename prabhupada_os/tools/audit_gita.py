import sqlite3
import os
import sys
import json

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "vedabase.db")

# Standard Gita Structure (Chapter: Verse Count)
# Based on 700 verses total.
EXPECTED_COUNTS = {
    1: 47,  # sometimes 46
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
    13: 35, # sometimes 34
    14: 27,
    15: 20,
    16: 24,
    17: 28,
    18: 78
}

def audit_database():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=== PRABHUPADA OS DATA AUDIT ===")
    print(f"Database: {DB_PATH}\n")

    total_missing = 0
    total_found = 0
    
    # Check Chapter by Chapter
    for chapter_num, expected_count in EXPECTED_COUNTS.items():
        cursor.execute(
            "SELECT verse FROM verses WHERE book_code='BG' AND chapter=?", 
            (chapter_num,)
        )
        verses = [row[0] for row in cursor.fetchall()]
        found_count = len(verses)
        total_found += found_count
        
        # Analyze missing verses
        # We expect verses to be strings like "1", "2", "3"...
        # But sometimes they are "1-2" (combined).
        
        # Create a set of "covered" numbers
        covered_numbers = set()
        for v in verses:
            parts = v.split('-')
            if len(parts) == 1:
                if parts[0].isdigit():
                    covered_numbers.add(int(parts[0]))
            elif len(parts) == 2:
                # Handle ranges like 1-2
                if parts[0].isdigit() and parts[1].isdigit():
                    start = int(parts[0])
                    end = int(parts[1])
                    for i in range(start, end + 1):
                        covered_numbers.add(i)
        
        missing_numbers = []
        for i in range(1, expected_count + 1):
            if i not in covered_numbers:
                missing_numbers.append(i)
        
        status = "OK" if not missing_numbers else "MISSING"
        if found_count > expected_count: status = "EXTRA" # Rare, but possible if splits happen
        
        print(f"Chapter {chapter_num:02d}: Found {found_count}/{expected_count} ... {status}")
        
        if missing_numbers:
            print(f"  -> Missing Verses: {missing_numbers}")
            total_missing += len(missing_numbers)
            
    print("\n=== SUMMARY ===")
    print(f"Total Expected: 700")
    print(f"Total Found:    {total_found}")
    print(f"Total Missing:  {total_missing}")
    
    conn.close()

if __name__ == "__main__":
    audit_database()
