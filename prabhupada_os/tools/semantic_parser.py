#!/usr/bin/env python3
"""
Semantic EPUB Parser - The Matrix (Pragmatic Edition)
Uses proven regex extraction + knowledge graph rules.
"""
import zipfile
import sqlite3
import re
import yaml
import hashlib
import os
from collections import defaultdict

class SemanticParser:
    """Semantic EPUB parser using knowledge graph"""
    
    def __init__(self, patterns_file, rules_file):
        self.patterns = self._load_yaml(patterns_file)
        self.rules = self._load_yaml(rules_file)
        self.word_to_num = self.rules.get('word_to_number', {})
        
        # Knowledge graph
        self.graph = {
            'chapters': defaultdict(lambda: {'files': set(), 'verses': set()}),
            'verses': [],
        }
        
    def _load_yaml(self, filepath):
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    
    def parse(self, epub_path, db_path):
        """Main parsing pipeline"""
        print("🚀 Starting Semantic Parse...")
        print(f"EPUB: {epub_path}")
        print(f"DB: {db_path}\\n")
        
        # Initialize database
        self._init_db(db_path)
        
        # Process EPUB using file-to-chapter map from patterns
        file_map = self.patterns.get('file_chapter_map', {})
        
        with zipfile.ZipFile(epub_path, 'r') as z:
            files = sorted([f for f in z.namelist() if f.endswith('.html') and 'part' in f])
            
            current_chapter = 0
            
            for filepath in files:
                content = z.read(filepath).decode('utf-8', errors='ignore')
                
                # Use file map if available, otherwise detect
                if filepath in file_map:
                    current_chapter = file_map[filepath]
                else:
                    detected = self._detect_chapter(content, current_chapter)
                    if detected:
                        current_chapter = detected
                
                # Skip if no chapter yet
                if current_chapter == 0:
                    continue
                
                # Extract verses using regex (proven method from analyzer)
                verse_refs = re.findall(r'TEXT\\s+([\\d\\-]+)', content, re.IGNORECASE)
                
                for verse_ref in verse_refs:
                    self._process_verse_ref(verse_ref, current_chapter, filepath, content)
        
        # Validate
        self._validate()
        
        # Export to DB
        self._export_to_db(db_path)
        
        print("\\n✅ Semantic Parse Complete!")
        
    def _detect_chapter(self, content, current_chapter):
        """Detect chapter using pattern matching rules"""
        # Rule R001: Word-based detection
        match = re.search(r'CHAPTER\\s+(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN|SIXTEEN|SEVENTEEN|EIGHTEEN)', 
                         content, re.IGNORECASE)
        if match:
            word = match.group(1).upper()
            if word in self.word_to_num:
                return self.word_to_num[word]
        
        # Rule R002: Numeric detection
        match = re.search(r'CHAPTER\\s+(\\d+)', content, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Rule R003: Continuation (use previous chapter)
        return current_chapter if current_chapter > 0 else 0
    
    def _process_verse_ref(self, verse_ref, chapter, filepath, content):
        """Process a verse reference (handles ranges)"""
        # Check if it's a range
        if '-' in verse_ref:
            try:
                start, end = map(int, verse_ref.split('-'))
                verse_numbers = list(range(start, end + 1))
            except:
                return
        else:
            try:
                verse_numbers = [int(verse_ref)]
            except:
                return
        
        # For each verse in the range, create an entry
        for verse_num in verse_numbers:
            # Extract content around this verse (simple heuristic)
            # Look for the verse pattern and grab surrounding text
            pattern = f"TEXT\\s+{verse_ref}"
            match = re.search(pattern, content, re.IGNORECASE)
            
            if match:
                # Extract a chunk of text after the verse marker
                start_pos = match.end()
                chunk = content[start_pos:start_pos+2000]  # Get next 2000 chars
                
                # Simple extraction: grab text until next TEXT marker or end
                next_text = re.search(r'TEXT\\s+\\d', chunk)
                if next_text:
                    verse_content = chunk[:next_text.start()].strip()
                else:
                    verse_content = chunk.strip()
                
                verse_entry = {
                    'book_code': 'BG',
                    'chapter': chapter,
                    'verse': str(verse_num),
                    'reference': f"BG {chapter}.{verse_num}",
                    'sanskrit': '',  # Would need more sophisticated extraction
                    'synonyms': '',
                    'translation': verse_content[:500] if verse_content else '',  # Use chunk as translation for now
                    'purport': '',
                    'file': filepath
                }
                
                self.graph['verses'].append(verse_entry)
                self.graph['chapters'][chapter]['files'].add(filepath)
                self.graph['chapters'][chapter]['verses'].add(verse_num)
    
    def _validate(self):
        """Validate using semantic rules"""
        print("🔍 Validating...")
        
        expected_structure = self.patterns['structure']['chapter_verse_counts']
        
        # Rule R201: Validate chapter count
        found_chapters = len(self.graph['chapters'])
        expected_chapters = self.patterns['structure']['total_chapters']
        print(f"Chapters: {found_chapters}/{expected_chapters}")
        
        # Rule R202: Validate total verse count
        total_verses = len(self.graph['verses'])
        expected_total = self.patterns['structure']['total_verses']
        print(f"Total Verses: {total_verses}/{expected_total}")
        
        # Rule R203: Validate verse sequences per chapter
        for chapter in sorted(self.graph['chapters'].keys()):
            verses = sorted(self.graph['chapters'][chapter]['verses'])
            expected_count = expected_structure.get(chapter, 0)
            actual_count = len(verses)
            
            # Check for gaps
            if verses:
                expected_sequence = list(range(1, expected_count + 1))
                missing = set(expected_sequence) - set(verses)
                status = "✓" if not missing else f"Missing: {sorted(missing)[:5]}"
                print(f"  Chapter {chapter:2d}: {actual_count:3d}/{expected_count:3d} {status}")
    
    def _init_db(self, db_path):
        """Initialize database"""
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
        conn.close()
    
    def _export_to_db(self, db_path):
        """Export parsed verses to database"""
        print("\\n💾 Exporting to database...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        inserted = 0
        skipped = 0
        
        for verse in self.graph['verses']:
            # Compute hash
            content = f"{verse['sanskrit']}|{verse['translation']}|{verse['purport']}"
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            
            try:
                cursor.execute('''
                    INSERT INTO verses (book_code, chapter, verse, sanskrit, synonyms, translation, purport, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    verse['book_code'],
                    verse['chapter'],
                    verse['verse'],
                    verse['sanskrit'],
                    verse['synonyms'],
                    verse['translation'],
                    verse['purport'],
                    content_hash
                ))
                inserted += 1
            except sqlite3.IntegrityError:
                skipped += 1
        
        conn.commit()
        conn.close()
        
        print(f"Inserted: {inserted}, Skipped (duplicates): {skipped}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    patterns_file = os.path.join(base_dir, 'patterns', 'gita_patterns.yaml')
    rules_file = os.path.join(base_dir, 'cortex', 'epub_knowledge', 'parsing_rules.yaml')
    epub_path = os.path.join(base_dir, '..', 'epub', 'Bhagavad-Gita As It Is (Original 1972 Edition).epub')
    db_path = os.path.join(base_dir, 'vedabase.db')
    
    parser = SemanticParser(patterns_file, rules_file)
    parser.parse(epub_path, db_path)

if __name__ == "__main__":
    main()

    """HTML parser for extracting verse content"""
    def __init__(self):
        super().__init__()
        self.in_verse_text = False
        self.in_sanskrit = False
        self.in_synonyms = False
        self.in_translation = False
        self.in_purport = False
        
        self.verses = []
        self.current_data = {}
        self.text_buffer = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        class_name = attrs_dict.get("class", "")
        
        if tag == "div":
            if "verse-text" in class_name:
                self.in_verse_text = True
                self.text_buffer = []
            elif "verse" in class_name and "verse-text" not in class_name:
                self.in_sanskrit = True
                self.text_buffer = []
            elif "word-mean" in class_name:
                self.in_synonyms = True
                self.text_buffer = []
            elif "data-trs" in class_name:
                self.in_translation = True
                self.text_buffer = []
            elif "purport" in class_name:
                self.in_purport = True
                self.text_buffer = []

    def handle_endtag(self, tag):
        if tag == "div":
            if self.in_verse_text:
                self.in_verse_text = False
                self.current_data["reference"] = "".join(self.text_buffer).strip()
            elif self.in_sanskrit:
                self.in_sanskrit = False
                self.current_data["sanskrit"] = "\\n".join(self.text_buffer).strip()
            elif self.in_synonyms:
                self.in_synonyms = False
                self.current_data["synonyms"] = "".join(self.text_buffer).strip()
            elif self.in_translation:
                self.in_translation = False
                self.current_data["translation"] = "".join(self.text_buffer).strip()
            elif self.in_purport:
                self.in_purport = False
                self.current_data["purport"] = "\\n".join(self.text_buffer).strip()
                if "translation" in self.current_data:
                    self.verses.append(self.current_data)
                    self.current_data = {}

    def handle_data(self, data):
        if any([self.in_verse_text, self.in_sanskrit, self.in_synonyms, 
                self.in_translation, self.in_purport]):
            self.text_buffer.append(data)

class SemanticParser:
    """Semantic EPUB parser using knowledge graph"""
    
    def __init__(self, patterns_file, rules_file):
        self.patterns = self._load_yaml(patterns_file)
        self.rules = self._load_yaml(rules_file)
        self.word_to_num = self.rules.get('word_to_number', {})
        
        # Knowledge graph
        self.graph = {
            'chapters': {},  # chapter_num -> {files: [], verses: []}
            'files': {},     # filepath -> {chapter: int, verses: []}
            'verses': [],    # all verses
        }
        
    def _load_yaml(self, filepath):
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    
    def parse(self, epub_path, db_path):
        """Main parsing pipeline"""
        print("🚀 Starting Semantic Parse...")
        print(f"EPUB: {epub_path}")
        print(f"DB: {db_path}\n")
        
        # Initialize database
        self._init_db(db_path)
        
        # Process EPUB
        with zipfile.ZipFile(epub_path, 'r') as z:
            files = sorted([f for f in z.namelist() if f.endswith('.html') and 'part' in f])
            
            current_chapter = 0
            
            for filepath in files:
                content = z.read(filepath).decode('utf-8', errors='ignore')
                
                # Detect chapter using rules
                detected_chapter = self._detect_chapter(content, current_chapter)
                if detected_chapter:
                    current_chapter = detected_chapter
                
                # Skip if no chapter yet
                if current_chapter == 0:
                    continue
                
                # Extract verses
                parser = GitaHTMLParser()
                parser.feed(content)
                
                for verse_data in parser.verses:
                    self._process_verse(verse_data, current_chapter, filepath)
        
        # Validate
        self._validate()
        
        # Export to DB
        self._export_to_db(db_path)
        
        print("\n✅ Semantic Parse Complete!")
        
    def _detect_chapter(self, content, current_chapter):
        """Detect chapter using pattern matching rules"""
        # Rule R001: Word-based detection
        match = re.search(r'CHAPTER\\s+(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN|SIXTEEN|SEVENTEEN|EIGHTEEN)', 
                         content, re.IGNORECASE)
        if match:
            word = match.group(1).upper()
            if word in self.word_to_num:
                return self.word_to_num[word]
        
        # Rule R002: Numeric detection
        match = re.search(r'CHAPTER\\s+(\\d+)', content, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Rule R003: Continuation (use previous chapter)
        return current_chapter if current_chapter > 0 else 0
    
    def _process_verse(self, verse_data, chapter, filepath):
        """Process a single verse using rules"""
        reference = verse_data.get('reference', '')
        
        # Extract verse number using Rule R101 and R102
        match = re.search(r'TEXT\\s+(\\d+)-(\\d+)', reference, re.IGNORECASE)
        if match:
            # Rule R102: Expand range
            start, end = int(match.group(1)), int(match.group(2))
            verse_numbers = list(range(start, end + 1))
        else:
            match = re.search(r'TEXT\\s+(\\d+)', reference, re.IGNORECASE)
            if match:
                # Rule R101: Single verse
                verse_numbers = [int(match.group(1))]
            else:
                return  # No verse number found
        
        # Create verse entries
        for verse_num in verse_numbers:
            verse_ref = f"BG {chapter}.{verse_num}"
            
            verse_entry = {
                'book_code': 'BG',
                'chapter': chapter,
                'verse': str(verse_num),
                'reference': verse_ref,
                'sanskrit': verse_data.get('sanskrit', ''),
                'synonyms': verse_data.get('synonyms', ''),
                'translation': verse_data.get('translation', ''),
                'purport': verse_data.get('purport', ''),
                'file': filepath
            }
            
            self.graph['verses'].append(verse_entry)
            
            # Update chapter tracking
            if chapter not in self.graph['chapters']:
                self.graph['chapters'][chapter] = {'files': set(), 'verses': []}
            self.graph['chapters'][chapter]['files'].add(filepath)
            self.graph['chapters'][chapter]['verses'].append(verse_num)
    
    def _validate(self):
        """Validate using semantic rules"""
        print("🔍 Validating...")
        
        expected_structure = self.patterns['structure']['chapter_verse_counts']
        
        # Rule R201: Validate chapter count
        found_chapters = len(self.graph['chapters'])
        expected_chapters = self.patterns['structure']['total_chapters']
        print(f"Chapters: {found_chapters}/{expected_chapters}")
        
        # Rule R202: Validate total verse count
        total_verses = len(self.graph['verses'])
        expected_total = self.patterns['structure']['total_verses']
        print(f"Total Verses: {total_verses}/{expected_total}")
        
        # Rule R203: Validate verse sequences per chapter
        for chapter, data in sorted(self.graph['chapters'].items()):
            verses = sorted(set(data['verses']))
            expected_count = expected_structure.get(chapter, 0)
            actual_count = len(verses)
            
            # Check for gaps
            if verses:
                expected_sequence = list(range(1, expected_count + 1))
                missing = set(expected_sequence) - set(verses)
                if missing:
                    print(f"  Chapter {chapter}: {actual_count}/{expected_count} - Missing: {sorted(missing)}")
                else:
                    print(f"  Chapter {chapter}: {actual_count}/{expected_count} ✓")
    
    def _init_db(self, db_path):
        """Initialize database"""
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
        conn.close()
    
    def _export_to_db(self, db_path):
        """Export parsed verses to database"""
        print("\n💾 Exporting to database...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        inserted = 0
        skipped = 0
        
        for verse in self.graph['verses']:
            # Compute hash
            content = f"{verse['sanskrit']}|{verse['translation']}|{verse['purport']}"
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            
            try:
                cursor.execute('''
                    INSERT INTO verses (book_code, chapter, verse, sanskrit, synonyms, translation, purport, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    verse['book_code'],
                    verse['chapter'],
                    verse['verse'],
                    verse['sanskrit'],
                    verse['synonyms'],
                    verse['translation'],
                    verse['purport'],
                    content_hash
                ))
                inserted += 1
            except sqlite3.IntegrityError:
                skipped += 1
        
        conn.commit()
        conn.close()
        
        print(f"Inserted: {inserted}, Skipped: {skipped}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    patterns_file = os.path.join(base_dir, 'patterns', 'gita_patterns.yaml')
    rules_file = os.path.join(base_dir, 'cortex', 'epub_knowledge', 'parsing_rules.yaml')
    epub_path = os.path.join(base_dir, '..', 'epub', 'Bhagavad-Gita As It Is (Original 1972 Edition).epub')
    db_path = os.path.join(base_dir, 'vedabase.db')
    
    parser = SemanticParser(patterns_file, rules_file)
    parser.parse(epub_path, db_path)

if __name__ == "__main__":
    main()
