#!/usr/bin/env python3
"""
Prabhupada ParserOS Kernel v1.0
The robust, catalog-driven extraction engine for Bhagavad-Gita.
"""
import json
import sqlite3
import zipfile
import re
import os
import hashlib
from bs4 import BeautifulSoup

class ExtractionStrategy:
    """Base class for extraction strategies"""
    def extract(self, html_snippet, verse_info):
        raise NotImplementedError

class StandardStrategy(ExtractionStrategy):
    """Extracts standard verse structure (verse-trs, word-mean, data-trs, purport)"""
    def extract(self, html_snippet, verse_info):
        soup = BeautifulSoup(html_snippet, 'html.parser')
        
        # Sanskrit
        sanskrit_divs = soup.find_all('div', class_=lambda c: c and 'verse-trs' in c)
        sanskrit = '\n'.join([div.get_text(strip=True) for div in sanskrit_divs])
        
        # Synonyms
        synonyms_div = soup.find('div', class_=lambda c: c and 'word-mean' in c)
        synonyms = synonyms_div.get_text(strip=True) if synonyms_div else ''
        
        # Translation
        # Try standard data-trs
        translation_div = soup.find('div', class_=lambda c: c and 'data-trs' in c)
        if translation_div:
            translation = translation_div.get_text(strip=True)
        else:
            # Try finding translation header and following text
            # Find all verse-hed divs first, then check text
            verse_heds = soup.find_all('div', class_=lambda c: c and 'verse-hed' in c)
            trans_header = None
            for hed in verse_heds:
                if 'TRANSLATION' in hed.get_text(strip=True).upper():
                    trans_header = hed
                    break
            
            if trans_header:
                # Get text between TRANSLATION and PURPORT
                translation = ''
                curr = trans_header.find_next_sibling()
                while curr:
                    # Stop if we hit PURPORT header
                    if curr.name == 'div' and 'verse-hed' in (curr.get('class') or []) and 'PURPORT' in curr.get_text(strip=True).upper():
                        break
                    
                    if curr.name == 'div' and 'purport' in (curr.get('class') or []):
                        # Check for bold text in purport (common pattern)
                        bold = curr.find('b')
                        if bold:
                            translation += bold.get_text(strip=True) + " "
                        else:
                            # If no bold, maybe the whole div is translation if it's before purport header
                            # But be careful not to grab purport text
                            pass 
                    curr = curr.find_next_sibling()
                translation = translation.strip()
            else:
                translation = ''

        # Purport
        purport_parts = []
        # Find purport header
        purport_header = None
        verse_heds = soup.find_all('div', class_=lambda c: c and 'verse-hed' in c)
        for hed in verse_heds:
            if 'PURPORT' in hed.get_text(strip=True).upper():
                purport_header = hed
                break
        
        if purport_header:
            curr = purport_header.find_next_sibling()
            while curr:
                # Stop if we hit next verse marker (though snippet should handle this)
                if curr.name == 'div' and 'verse-text' in (curr.get('class') or []):
                    break
                    
                if curr.name == 'div' and 'purport' in (curr.get('class') or []):
                    text = curr.get_text(strip=True)
                    # Remove translation if it was embedded in bold
                    if translation and translation in text:
                        text = text.replace(translation, '').strip()
                    if text:
                        purport_parts.append(text)
                curr = curr.find_next_sibling()
        
        purport = '\n\n'.join(purport_parts)
        
        return {
            'sanskrit': sanskrit,
            'synonyms': synonyms,
            'translation': translation,
            'purport': purport
        }

class BoldTranslationStrategy(ExtractionStrategy):
    """Extracts verses where translation is bolded inside a purport div"""
    def extract(self, html_snippet, verse_info):
        soup = BeautifulSoup(html_snippet, 'html.parser')
        
        # Sanskrit & Synonyms same as standard
        sanskrit_divs = soup.find_all('div', class_=lambda c: c and 'verse-trs' in c)
        sanskrit = '\n'.join([div.get_text(strip=True) for div in sanskrit_divs])
        
        synonyms_div = soup.find('div', class_=lambda c: c and 'word-mean' in c)
        synonyms = synonyms_div.get_text(strip=True) if synonyms_div else ''
        
        # Translation: Look for BOLD text in purport div
        translation = ''
        purport_divs = soup.find_all('div', class_=lambda c: c and 'purport' in c)
        
        for div in purport_divs:
            bold = div.find('b')
            if bold:
                translation = bold.get_text(strip=True)
                break
        
        # Purport: Everything else
        purport_parts = []
        for div in purport_divs:
            text = div.get_text(strip=True)
            if translation and translation in text:
                text = text.replace(translation, '').strip()
            if text:
                purport_parts.append(text)
        
        purport = '\n\n'.join(purport_parts)
        
        return {
            'sanskrit': sanskrit,
            'synonyms': synonyms,
            'translation': translation,
            'purport': purport
        }

class ParserOS:
    def __init__(self, epub_path, db_path, catalog_path):
        self.epub_path = epub_path
        self.db_path = db_path
        self.catalog_path = catalog_path
        self.strategies = [StandardStrategy(), BoldTranslationStrategy()]
        
    def load_catalog(self):
        with open(self.catalog_path, 'r') as f:
            return json.load(f)
            
    def get_verse_snippet(self, content, verse_info, next_verse_info=None):
        """Extract the raw HTML chunk for this verse"""
        marker = verse_info['parent_marker']
        
        # Find start position
        # We use the position from catalog if available, or search
        start_pos = verse_info.get('position')
        if start_pos is None:
             match = re.search(r'TEXT(?:S)?\s+' + re.escape(marker), content)
             start_pos = match.start() if match else -1
             
        if start_pos == -1:
            return ""
            
        # Find end position (start of next verse or end of file)
        if next_verse_info and next_verse_info['file'] == verse_info['file']:
            next_marker = next_verse_info['parent_marker']
            next_match = re.search(r'TEXT(?:S)?\s+' + re.escape(next_marker), content[start_pos+10:])
            if next_match:
                end_pos = start_pos + 10 + next_match.start()
            else:
                end_pos = len(content)
        else:
            end_pos = len(content)
            
        return content[start_pos:end_pos]

    def run(self):
        print("🚀 Starting ParserOS Kernel...")
        
        # Initialize DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS verses')
        cursor.execute('''
            CREATE TABLE verses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_code TEXT,
                chapter INTEGER,
                verse TEXT,
                sanskrit TEXT,
                synonyms TEXT,
                translation TEXT,
                purport TEXT,
                content_hash TEXT,
                UNIQUE(book_code, chapter, verse)
            )
        ''')
        
        catalog = self.load_catalog()
        verse_ids = sorted(catalog.keys(), key=lambda x: (catalog[x]['chapter'], int(catalog[x]['verse'])))
        
        success_count = 0
        
        with zipfile.ZipFile(self.epub_path, 'r') as z:
            # Cache file content
            file_cache = {}
            
            for i, v_id in enumerate(verse_ids):
                info = catalog[v_id]
                
                # Get file content
                if info['file'] not in file_cache:
                    file_cache[info['file']] = z.read(info['file']).decode('utf-8', errors='ignore')
                content = file_cache[info['file']]
                
                # Get next verse info for boundary
                next_info = None
                if i + 1 < len(verse_ids):
                    next_id = verse_ids[i+1]
                    next_info = catalog[next_id]
                
                # Extract snippet
                snippet = self.get_verse_snippet(content, info, next_info)
                
                # Try strategies
                verse_data = None
                for strategy in self.strategies:
                    try:
                        data = strategy.extract(snippet, info)
                        if data['sanskrit'] and data['translation']:
                            verse_data = data
                            break
                        # If standard failed (no translation), try bold
                        if not data['translation']:
                            continue
                    except Exception as e:
                        continue
                
                # Fallback: If no strategy worked perfectly, take the best result
                if not verse_data:
                    # Just use standard output even if incomplete
                    verse_data = self.strategies[0].extract(snippet, info)
                
                # Insert
                content_hash = hashlib.sha256(f"{v_id}|{verse_data['translation']}".encode()).hexdigest()
                cursor.execute('''
                    INSERT INTO verses (book_code, chapter, verse, sanskrit, synonyms, translation, purport, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'BG',
                    info['chapter'],
                    info['verse'],
                    verse_data['sanskrit'],
                    verse_data['synonyms'],
                    verse_data['translation'],
                    verse_data['purport'],
                    content_hash
                ))
                success_count += 1
                
                if i % 50 == 0:
                    print(f"Processed {i}/{len(verse_ids)} verses...")
        
        conn.commit()
        conn.close()
        print(f"✅ ParserOS finished. Imported {success_count} verses.")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    knowledge_dir = os.path.dirname(script_dir)
    prabhupada_os_dir = os.path.dirname(knowledge_dir)
    base_dir = os.path.dirname(prabhupada_os_dir)
    
    epub_path = os.path.join(base_dir, 'epub', 'Bhagavad-Gita As It Is (Original 1972 Edition).epub')
    db_path = os.path.join(knowledge_dir, 'store', 'vedabase.db')
    catalog_path = os.path.join(script_dir, 'verse_catalog.json')
    
    os_kernel = ParserOS(epub_path, db_path, catalog_path)
    os_kernel.run()
