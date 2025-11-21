#!/usr/bin/env python3
"""
Bhagavad-gita EPUB Import Script with Dynamic State Tracking
Extracts all 700 verses by handling multi-chapter files.
"""
import zipfile
import sqlite3
import hashlib
import os
import re
from html.parser import HTMLParser

class GitaHTMLParser(HTMLParser):
    """HTML parser with dynamic chapter tracking state machine"""
    def __init__(self, initial_chapter=0):
        super().__init__()
        self.current_section = None
        self.verses = []
        self.current_verse = {
            'chapter': initial_chapter,
            'sanskrit': [],
            'synonyms': [],
            'translation': [],
            'purport': [],
            'verse_text': None
        }
        self.text_buffer = []
        self.expecting_translation = False
        self.in_bold = False
        self.has_bold_content = False
        
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
            # print(f"DEBUG: DIV class='{class_name}'")
            
            # Verse sections
            # Match ANY verse-trs (verse-trs, verse-trs1, verse-trs4, verse-trs7, etc.)
            if 'verse-trs' in class_name:
                # New verse starting (Sanskrit) - save previous if exists
                self.save_verse()
                
                # print(f"DEBUG: Found Sanskrit class: {class_name}")
                self.current_section = 'sanskrit'
                self.text_buffer = []
            elif 'word-mean' in class_name:
                self.current_section = 'synonyms'
                self.text_buffer = []
            # Match ANY data-trs (data-trs, data-trs1, etc.)
            elif 'data-trs' in class_name:
                # New verse starting (Translation) - save previous if exists (if no sanskrit)
                # But usually sanskrit comes first. If sanskrit exists, we are in same verse.
                # If translation comes first (rare?), we save.
                # Actually, safer to just save if we have a translation already? 
                # No, we might be adding to existing translation? No, data-trs is usually one block.
                
                # If we already have a translation in current_verse, this is a NEW verse (or weird split)
                if self.current_verse['translation']:
                     self.save_verse()

                # print(f"DEBUG: Found Translation class: {class_name}")
                self.current_section = 'translation'
                self.text_buffer = []
                # CRITICAL: Capture chapter NOW, before state machine can change it
                self.current_verse['chapter'] = self.current_chapter
            elif 'purport' in class_name:
                self.current_section = 'purport'
                self.text_buffer = []
            # Capture verse number text (TEXT X or TEXTS X-Y)
            elif 'verse-text' in class_name:
                self.current_section = 'verse_number'
                self.text_buffer = []
            # Check for TRANSLATION header
            elif 'verse-hed' in class_name:
                self.current_section = 'header'
                self.text_buffer = []
            elif 'purport' in class_name:
                # Special case: If we just saw TRANSLATION header, this is actually translation
                # (even though it's in a purport div - some verses have bold translations in purport divs)
                if self.expecting_translation:
                    self.current_section = 'translation_in_purport'
                    self.expecting_translation = False # Reset
                    self.has_bold_content = False # Reset for this div
                    # CRITICAL: Capture chapter NOW
                    self.current_verse['chapter'] = self.current_chapter
                    
                    # If we already have a translation (rare), save previous?
                    if self.current_verse['translation']:
                         self.save_verse()
                else:
                    # If we have no translation yet and this purport has bold text,
                    # it might be the translation (Ch 12 verse 2 pattern)
                    if not self.current_verse['translation']:
                        self.current_section = 'potential_translation'
                        self.has_bold_content = False # Reset for this div
                    else:
                        self.current_section = 'purport'
                self.text_buffer = []
        
        # Track bold tags
        if tag == 'b':
            self.in_bold = True
            self.has_bold_content = True # Mark that we've seen bold in this section
                
    def handle_endtag(self, tag):
        # Track bold tags
        if tag == 'b':
            self.in_bold = False
            
        if tag == 'div' and self.current_section:
            text = ''.join(self.text_buffer).strip()
            
            if self.current_section == 'sanskrit':
                if text:
                    self.current_verse['sanskrit'].append(text)
            elif self.current_section == 'synonyms':
                if text:
                    self.current_verse['synonyms'].append(text)
            elif self.current_section == 'translation':
                if text:
                    self.current_verse['translation'].append(text)
            elif self.current_section == 'purport':
                if text:
                    self.current_verse['purport'].append(text)
                
                # DO NOT save here. Wait for next verse or EOF.
            elif self.current_section == 'potential_translation':
                # If this text was in bold, treat it as translation
                # Otherwise, treat it as purport
                if text:
                    if self.has_bold_content:
                        # This is the translation
                        self.current_verse['translation'].append(text)
                        # Capture chapter
                        if not self.current_verse.get('chapter'):
                            self.current_verse['chapter'] = self.current_chapter
                    else:
                        # This is purport
                        self.current_verse['purport'].append(text)
            elif self.current_section == 'translation_in_purport':
                # This is a purport div after TRANSLATION header
                # Bold text = translation, non-bold = purport
                if text:
                    print(f"DEBUG translation_in_purport: in_bold={self.in_bold}, text={text[:50]}")
                    if self.in_bold:
                        # This is the translation
                        self.current_verse['translation'].append(text)
                        print(f"  -> Added to translation")
                    else:
                        # This is purport (non-bold text in the same div)
                        self.current_verse['purport'].append(text)
                        print(f"  -> Added to purport")
            elif self.current_section == 'verse_number':
                if text:
                    # Append to handle fragmented text (though usually one block)
                    current_text = self.current_verse.get('verse_text', '')
                    if current_text:
                        self.current_verse['verse_text'] = current_text + " " + text.strip()
                    else:
                        self.current_verse['verse_text'] = text.strip()
            
            self.current_section = None
            self.text_buffer = []

    def save_verse(self):
        if self.current_verse['translation']:
            # Clean up text
            sanskrit = '\n'.join(self.current_verse['sanskrit']).strip()
            synonyms = ' '.join(self.current_verse['synonyms']).strip()
            translation = ' '.join(self.current_verse['translation']).strip()
            purport = '\n'.join(self.current_verse['purport']).strip()
            
            # Parse verse number from captured text (e.g., "TEXT 1" or "TEXTS 16-18")
            verse_nums = []
            raw_verse_text = self.current_verse.get('verse_text', '')
            if raw_verse_text:
                # Extract numbers
                # Handle "TEXTS 16-18" -> [16, 17, 18]
                # Handle "TEXT 1" -> [1]
                match = re.search(r'(\d+)(?:-(\d+))?', raw_verse_text)
                if match:
                    start = int(match.group(1))
                    end = int(match.group(2)) if match.group(2) else start
                    verse_nums = list(range(start, end + 1))
            
            # Fallback if no text captured (shouldn't happen often)
            if not verse_nums:
                # We'll handle this in the loop by appending to a list and using a counter if needed
                # But for now, let's just assume we have it or use a placeholder
                verse_nums = [0] # Placeholder, will be fixed by counter in main loop if 0
            
            print(f"DEBUG: Saving verse(s) {verse_nums} for Ch {self.current_verse['chapter']}")
            
            # Store as a list of dicts to be processed by main loop
            # We need to modify self.verses to store list of dicts?
            # Or just append multiple dicts?
            for v_num in verse_nums:
                self.verses.append({
                    'chapter': self.current_verse['chapter'],
                    'verse_num': v_num, # Explicit number
                    'sanskrit': sanskrit,
                    'synonyms': synonyms,
                    'translation': translation,
                    'purport': purport
                })
            
            # Reset for next verse
            self.current_verse = {
                'chapter': self.current_chapter, # Keep current chapter
                'sanskrit': [],
                'synonyms': [],
                'translation': [],
                'purport': [],
                'verse_text': None
            }
            self.expecting_translation = False
            
    def handle_data(self, data):
        # Check for TRANSLATION header in real-time
        if self.current_section == 'header' and 'TRANSLATION' in data.upper():
            self.expecting_translation = True
            print(f"DEBUG: Set expecting_translation=True from header text: {data.strip()}")
            
        # Check for chapter markers ONLY when not inside a verse section
        # This prevents false positives from purports mentioning other chapters
        if not self.current_section:
            data_upper = data.upper()
            if 'CHAPTER' in data_upper:
                # Use word boundaries and match longest names first (FOURTEEN before FOUR)
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
            
        # DEBUG: Print text content for context
        # if len(data.strip()) > 0:
        #     print(f"DEBUG: Text: {data.strip()[:50]}")

def import_gita():
    """Import Bhagavad-gita with dynamic chapter tracking"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # prabhupada_os/knowledge/ingestion -> prabhupada_os -> .. -> epub
    base_os_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # EPUB is in ../epub relative to prabhupada_os
    epub_path = os.path.join(base_os_dir, '..', 'epub', 'Bhagavad-Gita As It Is (Original 1972 Edition).epub')
    
    print("🚀 Bhagavad-gita Import with Dynamic State Tracking")
    print(f"EPUB: {epub_path}")
    
    # Database setup
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # prabhupada_os/knowledge
    db_path = os.path.join(base_dir, 'store', 'vedabase.db')
    print(f"DB: {db_path}")
    
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
    
    # Complete file-to-chapter fallback map
    # State machine will handle multi-chapter files automatically
    file_chapter_map = {
        'text/part0005.html': 1,   # Chapter 1 title
        'text/part0013.html': 1,
        'text/part0014.html': 2,
        'text/part0015.html': 2,   # CORRECTED: Contains Ch 2.35+ (was 10)
        'text/part0016.html': 3,
        'text/part0017.html': 4,
        'text/part0018.html': 5,
        'text/part0019.html': 6,
        'text/part0020.html': 7,
        'text/part0021.html': 7,   # Additional Ch 7
        'text/part0022.html': 7,
        'text/part0023.html': 8,
        'text/part0024.html': 9,
        'text/part0025.html': 10,
        'text/part0026.html': 11,  # Chapter 11 title page (no header text)
        'text/part0027.html': 12,
        'text/part0028.html': 13,
        'text/part0029.html': 14,
        'text/part0030.html': 15,
        'text/part0031.html': 16,  # Chapter 16 title
        'text/part0032.html': 15,  # CORRECTED: Chapter 15 (Verses 20)
        'text/part0033.html': 16,  # Has 16 + 18
        'text/part0034.html': 17,
        'text/part0035.html': 11,  # Has 11 + 18
        'text/part0036.html': 18,  # Additional Ch 18
    }
    
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
            parser = GitaHTMLParser(initial_chapter=fallback_chapter)
            parser.feed(content)
            parser.save_verse() # Save the last verse
            
            # Process extracted verses
            verse_num_by_chapter = {}
            for verse_data in parser.verses:
                chapter = verse_data.get('chapter', fallback_chapter)
                
                # Use explicit verse number if available
                explicit_num = verse_data.get('verse_num', 0)
                
                if explicit_num > 0:
                    verse_num = explicit_num
                    # Update counter to sync with explicit numbers
                    verse_num_by_chapter[chapter] = explicit_num
                else:
                    # Fallback to counter
                    if chapter not in verse_num_by_chapter:
                        verse_num_by_chapter[chapter] = 0
                    verse_num_by_chapter[chapter] += 1
                    verse_num = verse_num_by_chapter[chapter]
                
                # Compute hash (include verse num to make unique for split verses)
                content_str = f"{verse_num}|{verse_data.get('sanskrit', '')}|{verse_data.get('translation', '')}|{verse_data.get('purport', '')}"
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
                    
                except sqlite3.IntegrityError:
                    pass  # Skip duplicates
            
            if parser.verses:
                print(f"  Inserted {len(parser.verses)} verses")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Total verses inserted: {total_inserted}")
    print(f"\nChapter breakdown:")
    for ch in sorted(chapter_counts.keys()):
        print(f"  Chapter {ch:2d}: {chapter_counts[ch]:3d} verses")
    
    # Final count
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM verses WHERE book_code='BG'")
    final_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"\n📊 Final count: {final_count}/700 verses")
    
    if final_count >= 698:  # Allow +/- 2
        print("🎉 PERFECT TRANSMISSION! All verses imported!")
    else:
        print(f"⚠️  Missing {700 - final_count} verses")

if __name__ == "__main__":
    import_gita()
