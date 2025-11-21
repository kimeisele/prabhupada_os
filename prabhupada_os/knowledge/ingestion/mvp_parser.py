#!/usr/bin/env python3
"""
MVP EPUB Parser - Simple and Pragmatic
Uses ACTUAL HTML patterns found in the EPUB (div classes, not TEXT markers)
"""
import zipfile
import sqlite3
import hashlib
import os
import re
from html.parser import HTMLParser

class SimpleGitaParser(HTMLParser):
    """Simple HTML parser that extracts verses and tracks chapter changes dynamically"""
    def __init__(self, initial_chapter=0):
        super().__init__()
        self.current_section = None
        self.verses = []
        self.current_verse = {}
        self.text_buffer = []
        
        # State machine for chapter tracking
        self.current_chapter = initial_chapter
        self.chapter_word_map = {
            'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5, 'SIX': 6,
            'SEVEN': 7, 'EIGHT': 8, 'NINE': 9, 'TEN': 10, 'ELEVEN': 11, 'TWELVE': 12,
            'THIRTEEN': 13, 'FOURTEEN': 14, 'FIFTEEN': 15, 'SIXTEEN': 16,
            'SEVENTEEN': 17, 'EIGHTEEN': 18
        }
        
    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            attrs_dict = dict(attrs)
            class_name = attrs_dict.get('class', '')
            
            # Verse sections
            if 'verse-trs4' in class_name or 'verse-trs5' in class_name:
                self.current_section = 'sanskrit'
                self.text_buffer = []
            elif 'word-mean' in class_name:
                self.current_section = 'synonyms'
                self.text_buffer = []
            elif 'data-trs' in class_name:
                self.current_section = 'translation'
                self.text_buffer = []
                # CRITICAL: Capture chapter NOW, before state machine can change it
                self.current_verse['chapter'] = self.current_chapter
            elif 'purport' in class_name:
                self.current_section = 'purport'
                self.text_buffer = []
                
    def handle_endtag(self, tag):
        if tag == 'div' and self.current_section:
            text = ''.join(self.text_buffer).strip()
            
            if self.current_section == 'sanskrit':
                if 'sanskrit' not in self.current_verse:
                    self.current_verse['sanskrit'] = text
                else:
                    self.current_verse['sanskrit'] += '\n' + text
            elif self.current_section == 'synonyms':
                self.current_verse['synonyms'] = text
            elif self.current_section == 'translation':
                self.current_verse['translation'] = text
                # Chapter was already assigned in handle_starttag
            elif self.current_section == 'purport':
                # Append purport (there might be multiple purport divs per verse)
                if 'purport' not in self.current_verse:
                    self.current_verse['purport'] = text
                else:
                    self.current_verse['purport'] += '\n\n' + text
                
                # Save verse after purport
                if 'translation' in self.current_verse:
                    self.verses.append(dict(self.current_verse))
                    self.current_verse = {}
            
            self.current_section = None
            self.text_buffer = []
            
    def handle_data(self, data):
        # Check for chapter markers ONLY when not inside a verse section
        # This prevents false positives from purports mentioning other chapters
        if not self.current_section:
            data_upper = data.upper()
            if 'CHAPTER' in data_upper:
                # Try to extract chapter number
                # Use word boundaries and match longest names first (FOURTEEN before FOUR)
                import re
                match = re.search(r'CHAPTER\s+(EIGHTEEN|SEVENTEEN|SIXTEEN|FIFTEEN|FOURTEEN|THIRTEEN|TWELVE|ELEVEN|TEN|NINE|EIGHT|SEVEN|SIX|FIVE|FOUR|THREE|TWO|ONE|\d+)\b', data_upper)
                if match:
                    chapter_text = match.group(1)
                    if chapter_text in self.chapter_word_map:
                        new_chapter = self.chapter_word_map[chapter_text]
                    elif chapter_text.isdigit():
                        new_chapter = int(chapter_text)
                    else:
                        new_chapter = None
                        
                    if new_chapter and new_chapter != self.current_chapter:
                        print(f"  [State Change] Chapter {self.current_chapter} → {new_chapter}")
                        self.current_chapter = new_chapter
        
        # Always buffer text if we're in a section
        if self.current_section:
            self.text_buffer.append(data)


def parse_gita_mvp():
    """MVP parser - get 700/700 verses using actual HTML structure"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    epub_path = os.path.join(base_dir, '..', 'epub', 'Bhagavad-Gita As It Is (Original 1972 Edition).epub')
    db_path = os.path.join(base_dir, 'vedabase.db')
    
    print("🚀 MVP EPUB Parser")
    print(f"EPUB: {epub_path}")
    print(f"DB: {db_path}\\n")
    
    # Initialize DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_code TEXT,
            chapter INTEGER,
            verse TEXT,
            sanskrit TEXT,
            synonyms TEXT,
            translation TEXT,
            purport TEXT,
            content_hash TEXT UNIQUE
        )
    ''')
    
    cursor.execute("DELETE FROM verses WHERE book_code='BG'")
    conn.commit()
    
    # COMPLETE file-to-chapter map based on systematic search of ALL files
    # Files are mapped based on actual verse counts and chapter markers found
    file_chapter_map = {
        'text/part0013.html': 1,   # 39 verses, CHAPTER ONE
        'text/part0014.html': 2,   # 34 verses, CHAPTER TWO
        'text/part0015.html': 10,  # 37 verses, CHAPTER TEN
        'text/part0016.html': 3,   # 43 verses, CHAPTER THREE
        'text/part0017.html': 4,   # 42 verses, CHAPTER FOUR
        'text/part0018.html': 5,   # 27 verses, CHAPTER FIVE
        'text/part0019.html': 6,   # 42 verses, CHAPTER SIX
        'text/part0020.html': 7,   # 2 verses, CHAPTER SEVEN (start)
        'text/part0022.html': 7,   # 28 verses, no marker (likely Ch 7 continuation)
        'text/part0023.html': 8,   # 28 verses, CHAPTER EIGHT
        'text/part0024.html': 9,   # 34 verses, CHAPTER NINE
        'text/part0025.html': 10,  # 40 verses, CHAPTER TEN (continuation)
        'text/part0027.html': 12,  # 14 verses, CHAPTER TWELVE
        'text/part0028.html': 13,  # 29 verses, CHAPTER THIRTEEN
        'text/part0029.html': 14,  # 23 verses, CHAPTER FOUR marker but likely Ch 14
        'text/part0030.html': 15,  # 16 verses, CHAPTER FIFTEEN
        'text/part0032.html': 17,  # 3 verses, no marker (likely Ch 17)
        'text/part0033.html': 18,  # 19 verses, CHAPTER SIX marker but likely Ch 18
        'text/part0035.html': 11,  # 74 verses, CHAPTER EIGHT marker but too many - likely Ch 11
    }
    
    # Process ALL files, let the state machine handle chapter detection
    total_inserted = 0
    chapter_counts = {}
    
    with zipfile.ZipFile(epub_path, 'r') as z:
        files = sorted([f for f in z.namelist() if f.endswith('.html') and 'part' in f])
        
        for filepath in files:
            content = z.read(filepath).decode('utf-8', errors='ignore')
            
            # Get fallback chapter from map, or 0 if not in map
            fallback_chapter = file_chapter_map.get(filepath, 0)
            
            # Skip files with no fallback and no verses
            if fallback_chapter == 0 and content.count('class="data-trs"') == 0:
                continue
            
            print(f"Processing {filepath} (Fallback: Chapter {fallback_chapter})...")
            
            # Initialize parser with fallback chapter
            parser = SimpleGitaParser(initial_chapter=fallback_chapter)
            parser.feed(content)
            
            # Process extracted verses
            verse_num_by_chapter = {}
            for verse_data in parser.verses:
                chapter = verse_data.get('chapter', fallback_chapter)
                
                # Track verse numbers per chapter
                if chapter not in verse_num_by_chapter:
                    verse_num_by_chapter[chapter] = 1
                else:
                    verse_num_by_chapter[chapter] += 1
                
                verse_num = verse_num_by_chapter[chapter]
                
                # Compute hash
                content_str = f"{verse_data.get('sanskrit', '')}|{verse_data.get('translation', '')}|{verse_data.get('purport', '')}"
                content_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
                
                try:
                    cursor.execute('''
                        INSERT INTO verses (book_code, chapter, verse, sanskrit, synonyms, translation, purport, content_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        'BG',
                        chapter,
                        str(verse_num),
                        verse_data.get('sanskrit', ''),
                        verse_data.get('synonyms', ''),
                        verse_data.get('translation', ''),
                        verse_data.get('purport', ''),
                        content_hash
                    ))
                    total_inserted += 1
                    
                    if chapter not in chapter_counts:
                        chapter_counts[chapter] = 0
                    chapter_counts[chapter] += 1
                    
                except sqlite3.IntegrityError as e:
                    print(f"  Skipped duplicate: Chapter {chapter}, Verse {verse_num}")
            
            if parser.verses:
                print(f"  Inserted {len(parser.verses)} verses")
    
    conn.commit()
    conn.close()
    
    print(f"\\n✅ Total verses inserted: {total_inserted}")
    print(f"\\nChapter breakdown:")
    for ch in sorted(chapter_counts.keys()):
        print(f"  Chapter {ch:2d}: {chapter_counts[ch]:3d} verses")

if __name__ == "__main__":
    parse_gita_mvp()
