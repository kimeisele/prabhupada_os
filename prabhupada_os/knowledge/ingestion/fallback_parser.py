#!/usr/bin/env python3
"""
Fallback parser for the 4 missing verses with bold translations in purport divs.
This is a targeted "second pass" that handles the edge cases.
"""
import zipfile
import sqlite3
import hashlib
import re

def extract_missing_verses():
    """Extract the 4 missing verses with custom logic"""
    import os
    
    # Get to prototype_projects_monorepo from prabhupada_os/knowledge/ingestion/
    script_dir = os.path.dirname(os.path.abspath(__file__))  # .../prabhupada_os/knowledge/ingestion
    knowledge_dir = os.path.dirname(script_dir)  # .../prabhupada_os/knowledge
    prabhupada_os_dir = os.path.dirname(knowledge_dir)  # .../prabhupada_os
    base_dir = os.path.dirname(prabhupada_os_dir)  # .../prototype_projects_monorepo
    
    epub_path = os.path.join(base_dir, 'epub', 'Bhagavad-Gita As It Is (Original 1972 Edition).epub')
    db_path = os.path.join(knowledge_dir, 'store', 'vedabase.db')
    
    # Define the missing verses and their locations
    missing_verses = [
        # Original missing verses
        {'chapter': 11, 'verse': 2, 'file': 'text/part0026.html'},
        {'chapter': 11, 'verse': 8, 'file': 'text/part0026.html'},
        {'chapter': 12, 'verse': 2, 'file': 'text/part0027.html'},
        {'chapter': 12, 'verse': 5, 'file': 'text/part0027.html'},
        {'chapter': 12, 'verse': 11, 'file': 'text/part0027.html'},
        # Additional missing verse 2s
        {'chapter': 1, 'verse': 2, 'file': 'text/part0013.html'},
        {'chapter': 2, 'verse': 2, 'file': 'text/part0014.html'},
        {'chapter': 2, 'verse': 36, 'file': 'text/part0015.html'},
        {'chapter': 3, 'verse': 2, 'file': 'text/part0016.html'},
        {'chapter': 4, 'verse': 2, 'file': 'text/part0017.html'},
        {'chapter': 5, 'verse': 2, 'file': 'text/part0018.html'},
        {'chapter': 6, 'verse': 2, 'file': 'text/part0019.html'},
        {'chapter': 7, 'verse': 2, 'file': 'text/part0020.html'},
        {'chapter': 8, 'verse': 2, 'file': 'text/part0023.html'},
        {'chapter': 9, 'verse': 2, 'file': 'text/part0024.html'},
        {'chapter': 10, 'verse': 2, 'file': 'text/part0025.html'},
        {'chapter': 13, 'verse': 2, 'file': 'text/part0028.html'},
        {'chapter': 13, 'verse': 3, 'file': 'text/part0028.html'},
        {'chapter': 14, 'verse': 2, 'file': 'text/part0029.html'},
        {'chapter': 14, 'verse': 3, 'file': 'text/part0029.html'},
        {'chapter': 14, 'verse': 4, 'file': 'text/part0029.html'},
        {'chapter': 15, 'verse': 2, 'file': 'text/part0030.html'},
        {'chapter': 16, 'verse': 2, 'file': 'text/part0033.html'},
        {'chapter': 16, 'verse': 4, 'file': 'text/part0033.html'},
        {'chapter': 17, 'verse': 2, 'file': 'text/part0034.html'},
        {'chapter': 18, 'verse': 2, 'file': 'text/part0035.html'},
    ]
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    inserted = 0
    
    with zipfile.ZipFile(epub_path, 'r') as z:
        for verse_info in missing_verses:
            chapter = verse_info['chapter']
            verse_num = verse_info['verse']
            filepath = verse_info['file']
            
            content = z.read(filepath).decode('utf-8', errors='ignore')
            
            # Find the TEXT marker
            text_marker = f'TEXT {verse_num}'
            if text_marker not in content:
                print(f"Warning: Could not find {text_marker} in {filepath}")
                continue
            
            # Extract the verse section
            start = content.find(text_marker)
            # Find the next TEXT marker or end
            next_text = content.find('TEXT ', start + len(text_marker))
            if next_text == -1:
                snippet = content[start:]
            else:
                snippet = content[start:next_text]
            
            # Extract Sanskrit (verse-trs4/5/7/8)
            sanskrit_parts = []
            for match in re.finditer(r'<div class="verse-trs[4578]"[^>]*>(.*?)</div>', snippet, re.DOTALL):
                text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                if text:
                    sanskrit_parts.append(text)
            sanskrit = '\n'.join(sanskrit_parts)
            
            # Extract synonyms (word-mean)
            synonyms_parts = []
            word_mean_match = re.search(r'<div class="word-mean[^"]*"[^>]*>(.*?)</div>', snippet, re.DOTALL)
            if word_mean_match:
                # Clean HTML tags
                text = re.sub(r'<[^>]+>', ' ', word_mean_match.group(1))
                text = re.sub(r'\s+', ' ', text).strip()
                synonyms_parts.append(text)
            synonyms = ' '.join(synonyms_parts)
            
            # Extract translation (bold text in purport div after TRANSLATION header)
            translation = ''
            trans_match = re.search(r'TRANSLATION.*?<div class="purport[^"]*"[^>]*>.*?<b[^>]*>(.*?)</b>', snippet, re.DOTALL)
            if trans_match:
                translation = re.sub(r'<[^>]+>', '', trans_match.group(1)).strip()
            
            # Extract purport (non-bold text in purport divs after PURPORT header)
            purport_parts = []
            purport_section = re.search(r'PURPORT(.*)', snippet, re.DOTALL)
            if purport_section:
                purport_text = purport_section.group(1)
                # Find all purport divs
                for match in re.finditer(r'<div class="purport[^"]*"[^>]*>(.*?)</div>', purport_text, re.DOTALL):
                    # Remove bold tags and their content (that's the translation)
                    text = re.sub(r'<b[^>]*>.*?</b>', '', match.group(1))
                    # Clean remaining HTML
                    text = re.sub(r'<[^>]+>', ' ', text)
                    text = re.sub(r'\s+', ' ', text).strip()
                    if text and len(text) > 20:  # Avoid empty or very short fragments
                        purport_parts.append(text)
            purport = '\n'.join(purport_parts)
            
            # Compute hash
            content_str = f"{verse_num}|{sanskrit}|{translation}|{purport}"
            content_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
            
            # Insert into database
            try:
                cursor.execute('''
                    INSERT INTO verses (book_code, chapter, verse, sanskrit, synonyms, translation, purport, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'BG',
                    chapter,
                    str(verse_num),
                    sanskrit,
                    synonyms,
                    translation,
                    purport,
                    content_hash
                ))
                inserted += 1
                print(f"✓ Inserted BG {chapter}.{verse_num}")
            except sqlite3.IntegrityError:
                print(f"  Already exists: BG {chapter}.{verse_num}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Fallback parser inserted {inserted} verses")
    
    # Final count
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM verses WHERE book_code='BG'")
    final_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"📊 Final count: {final_count}/700 verses")
    
    if final_count >= 700:
        print("🎉 PERFECT! All 700 verses imported!")
    
    return final_count

if __name__ == "__main__":
    extract_missing_verses()
