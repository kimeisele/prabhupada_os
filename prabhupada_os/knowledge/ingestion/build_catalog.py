#!/usr/bin/env python3
"""
Build canonical verse catalog from EPUB TEXT markers.
This is the GROUND TRUTH for what verses exist and how they're organized.
"""
import zipfile
import json
import re
import os
from collections import defaultdict

def build_verse_catalog(epub_path):
    """Extract canonical verse list from TEXT/TEXTS markers in the EPUB"""
    
    # Use the proven file-to-chapter mapping
    file_chapter_map = {
        'text/part0005.html': 1,
        'text/part0013.html': 1,
        'text/part0014.html': 2,
        'text/part0015.html': 2,
        'text/part0016.html': 3,
        'text/part0017.html': 4,
        'text/part0018.html': 5,
        'text/part0019.html': 6,
        'text/part0020.html': 7,
        'text/part0021.html': 7,
        'text/part0022.html': 7,
        'text/part0023.html': 8,
        'text/part0024.html': 9,
        'text/part0025.html': 10,
        'text/part0026.html': 11,
        'text/part0027.html': 12,
        'text/part0028.html': 13,
        'text/part0029.html': 14,
        'text/part0030.html': 15,
        'text/part0031.html': 16,
        'text/part0032.html': 15,  # Chapter 15 continuation
        'text/part0033.html': 16,
        'text/part0034.html': 17,
        'text/part0035.html': 18,  # Chapter 18
        'text/part0036.html': 18,
    }
    
    catalog = {}
    chapter_counts = defaultdict(int)
    
    with zipfile.ZipFile(epub_path, 'r') as z:
        files = sorted([f for f in z.namelist() if f.endswith('.html') and 'part' in f])
        
        for filepath in files:
            # Get chapter from map
            current_chapter = file_chapter_map.get(filepath, 0)
            if current_chapter == 0:
                continue  # Skip files not in our map
            
            content = z.read(filepath).decode('utf-8', errors='ignore')
            
            # Handle multi-chapter files (part0033, part0035)
            # Detect chapter transitions within the file
            chapter_markers = re.findall(r'CHAPTER\s+(EIGHTEEN|SEVENTEEN|SIXTEEN|FIFTEEN|FOURTEEN|THIRTEEN|TWELVE|ELEVEN|TEN|NINE|EIGHT|SEVEN|SIX|FIVE|FOUR|THREE|TWO|ONE|\d+)', content.upper())
            # Handle multi-chapter files (part0033, part0035)
            # Detect chapter transitions within the file
            chapter_word_map = {
                'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5, 'SIX': 6,
                'SEVEN': 7, 'EIGHT': 8, 'NINE': 9, 'TEN': 10, 'ELEVEN': 11, 'TWELVE': 12,
                'THIRTEEN': 13, 'FOURTEEN': 14, 'FIFTEEN': 15, 'SIXTEEN': 16,
                'SEVENTEEN': 17, 'EIGHTEEN': 18
            }
            
            # Find all TEXT markers with their positions
            text_markers = []
            for match in re.finditer(r'TEXT(?:S)?\s+(\d+(?:-\d+)?)', content):
                text_markers.append({
                    'marker': match.group(1),
                    'position': match.start()
                })
            
            # Assign chapter to each TEXT marker
            # Since we verified files don't share chapters, we just use the file's chapter
            for text_info in text_markers:
                marker = text_info['marker']
                position = text_info['position']
                
                verse_id = f"BG {current_chapter}.{marker}"
                
                # Determine type and count
                if '-' in marker:
                    start, end = map(int, marker.split('-'))
                    # Create an entry for EACH verse in the range
                    for v_num in range(start, end + 1):
                        v_id = f"BG {current_chapter}.{v_num}"
                        catalog[v_id] = {
                            'chapter': current_chapter,
                            'verse': str(v_num),
                            'file': filepath,
                            'type': 'merged',
                            'parent_marker': marker,  # e.g. "16-18"
                            'position': position
                        }
                        chapter_counts[current_chapter] += 1
                else:
                    # Single verse
                    verse_id = f"BG {current_chapter}.{marker}"
                    catalog[verse_id] = {
                        'chapter': current_chapter,
                        'verse': marker,
                        'file': filepath,
                        'type': 'single',
                        'parent_marker': marker,
                        'position': position
                    }
                    chapter_counts[current_chapter] += 1
    
    return catalog, dict(chapter_counts)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    knowledge_dir = os.path.dirname(script_dir)
    prabhupada_os_dir = os.path.dirname(knowledge_dir)
    base_dir = os.path.dirname(prabhupada_os_dir)
    
    epub_path = os.path.join(base_dir, 'epub', 'Bhagavad-Gita As It Is (Original 1972 Edition).epub')
    output_path = os.path.join(script_dir, 'verse_catalog.json')
    
    print("📚 Building Canonical Verse Catalog from EPUB...\n")
    
    catalog, chapter_counts = build_verse_catalog(epub_path)
    
    # Sort catalog by chapter and verse
    sorted_catalog = dict(sorted(catalog.items(), key=lambda item: (item[1]['chapter'], int(item[1]['verse']))))
    
    # Save catalog
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_catalog, f, indent=2, ensure_ascii=False)
    
    # Print summary
    total_verses = len(sorted_catalog)
    
    print(f"✅ Catalog built successfully!")
    print(f"   Saved to: {output_path}\n")
    print(f"📊 Summary:")
    print(f"   Total canonical verses: {total_verses}")
    print(f"\n📖 Chapter breakdown:")
    
    expected = {
        1: 46, 2: 72, 3: 43, 4: 42, 5: 29, 6: 47, 7: 30, 8: 28, 9: 34,
        10: 42, 11: 55, 12: 20, 13: 35, 14: 27, 15: 20, 16: 24, 17: 28, 18: 78
    }
    
    for ch in sorted(chapter_counts.keys()):
        count = chapter_counts[ch]
        exp = expected.get(ch, '?')
        status = "✓" if count == exp else "✗"
        diff = count - exp if isinstance(exp, int) else 0
        diff_str = f" ({diff:+d})" if diff != 0 else ""
        print(f"   {status} Chapter {ch:2d}: {count:2d} verses (expected {exp}){diff_str}")
    
    print(f"\n{'='*60}")
    if total_verses == 700:
        print("🎉 PERFECT! Exactly 700 canonical verses!")
    else:
        print(f"⚠️  Found {total_verses} verses, expected 700")
    print(f"{'='*60}")
    
    return sorted_catalog

if __name__ == "__main__":
    main()
