#!/usr/bin/env python3
"""
EPUB Analyzer - Data-Driven Analysis Tool
Provides comprehensive analysis of EPUB structure for robust parsing.
"""
import zipfile
import re
import sys
import os
from collections import defaultdict

# Expected structure for Bhagavad-gita
EXPECTED_STRUCTURE = {
    1: 46, 2: 72, 3: 43, 4: 42, 5: 29, 6: 47, 7: 30, 8: 28, 9: 34,
    10: 42, 11: 55, 12: 20, 13: 35, 14: 27, 15: 20, 16: 24, 17: 28, 18: 78
}

class EPUBAnalyzer:
    def __init__(self, epub_path):
        self.epub_path = epub_path
        self.files = []
        self.file_analysis = {}
        self.chapter_map = {}
        self.verse_data = defaultdict(list)
        
    def analyze(self):
        """Run complete analysis"""
        print("=" * 80)
        print("EPUB STRUCTURE ANALYZER")
        print("=" * 80)
        print(f"Analyzing: {self.epub_path}\n")
        
        self._load_files()
        self._analyze_files()
        self._detect_chapters()
        self._extract_verses()
        self._validate()
        self._generate_recommendations()
        
    def _load_files(self):
        """Load and list all HTML files"""
        print("📁 FILE STRUCTURE")
        print("-" * 80)
        
        with zipfile.ZipFile(self.epub_path, 'r') as z:
            all_files = z.namelist()
            self.files = sorted([f for f in all_files if f.endswith('.html') and 'part' in f])
            
        print(f"Total HTML files: {len(self.files)}")
        print(f"File range: {self.files[0]} to {self.files[-1]}\n")
        
    def _analyze_files(self):
        """Analyze each file for content patterns"""
        print("🔍 FILE CONTENT ANALYSIS")
        print("-" * 80)
        
        with zipfile.ZipFile(self.epub_path, 'r') as z:
            for i, filepath in enumerate(self.files):
                content = z.read(filepath).decode('utf-8', errors='ignore')
                
                # Detect chapter markers
                chapter_patterns = {
                    'CHAPTER ONE': 'CHAPTER ONE' in content,
                    'CHAPTER TWO': 'CHAPTER TWO' in content,
                    'CHAPTER 1': 'CHAPTER 1' in content,
                    'calibre29': 'class="calibre29"' in content,
                    'calibre38': 'class="calibre38"' in content,
                }
                
                # Extract chapter numbers using regex
                chapter_matches = re.findall(r'CHAPTER\s+(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN|SIXTEEN|SEVENTEEN|EIGHTEEN|\d+)', content, re.IGNORECASE)
                
                # Extract verse references
                verse_matches = re.findall(r'TEXT\s+([\d\-]+)', content, re.IGNORECASE)
                
                self.file_analysis[filepath] = {
                    'index': i,
                    'size': len(content),
                    'chapter_patterns': {k: v for k, v in chapter_patterns.items() if v},
                    'chapter_matches': chapter_matches,
                    'verse_count': len(verse_matches),
                    'verses': verse_matches,
                    'has_verses': len(verse_matches) > 0
                }
                
        # Print summary
        files_with_chapters = sum(1 for f in self.file_analysis.values() if f['chapter_matches'])
        files_with_verses = sum(1 for f in self.file_analysis.values() if f['has_verses'])
        
        print(f"Files with chapter markers: {files_with_chapters}")
        print(f"Files with verses: {files_with_verses}\n")
        
    def _detect_chapters(self):
        """Create definitive file-to-chapter mapping"""
        print("📖 CHAPTER DETECTION")
        print("-" * 80)
        
        word_to_num = {
            'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5, 'SIX': 6,
            'SEVEN': 7, 'EIGHT': 8, 'NINE': 9, 'TEN': 10, 'ELEVEN': 11, 'TWELVE': 12,
            'THIRTEEN': 13, 'FOURTEEN': 14, 'FIFTEEN': 15, 'SIXTEEN': 16,
            'SEVENTEEN': 17, 'EIGHTEEN': 18
        }
        
        for filepath, analysis in self.file_analysis.items():
            if not analysis['chapter_matches']:
                continue
                
            # Get the first chapter match (most reliable)
            first_match = analysis['chapter_matches'][0].upper()
            
            if first_match in word_to_num:
                chapter_num = word_to_num[first_match]
            elif first_match.isdigit():
                chapter_num = int(first_match)
            else:
                continue
                
            if chapter_num not in self.chapter_map:
                self.chapter_map[chapter_num] = []
            self.chapter_map[chapter_num].append(filepath)
            
            # Store verses for this chapter
            if analysis['verses']:
                self.verse_data[chapter_num].extend(analysis['verses'])
        
        # Print chapter mapping
        for chapter in sorted(self.chapter_map.keys()):
            files = self.chapter_map[chapter]
            verse_count = len(self.verse_data[chapter])
            print(f"Chapter {chapter:2d}: {len(files)} file(s), {verse_count} verse refs")
            for f in files:
                print(f"  └─ {f}")
        print()
        
    def _extract_verses(self):
        """Analyze verse extraction patterns"""
        print("📜 VERSE EXTRACTION ANALYSIS")
        print("-" * 80)
        
        total_verse_refs = 0
        range_count = 0
        
        for chapter, verses in sorted(self.verse_data.items()):
            # Count ranges
            ranges = [v for v in verses if '-' in v]
            range_count += len(ranges)
            total_verse_refs += len(verses)
            
            # Expand ranges to get actual verse count
            expanded = set()
            for v in verses:
                if '-' in v:
                    try:
                        start, end = map(int, v.split('-'))
                        for i in range(start, end + 1):
                            expanded.add(i)
                    except:
                        expanded.add(v)
                else:
                    try:
                        expanded.add(int(v))
                    except:
                        pass
            
            expected = EXPECTED_STRUCTURE.get(chapter, 0)
            actual = len(expanded)
            status = "✓" if actual == expected else "✗"
            
            print(f"Chapter {chapter:2d}: {actual:3d}/{expected:3d} verses {status}")
            if ranges:
                print(f"  └─ {len(ranges)} range(s): {ranges[:5]}")
        
        print(f"\nTotal verse references: {total_verse_refs}")
        print(f"Verse ranges found: {range_count}\n")
        
    def _validate(self):
        """Validate against expected structure"""
        print("✅ VALIDATION REPORT")
        print("-" * 80)
        
        # Check chapters
        expected_chapters = set(EXPECTED_STRUCTURE.keys())
        found_chapters = set(self.chapter_map.keys())
        
        missing_chapters = expected_chapters - found_chapters
        extra_chapters = found_chapters - expected_chapters
        
        print(f"Expected chapters: {len(expected_chapters)}")
        print(f"Found chapters: {len(found_chapters)}")
        
        if missing_chapters:
            print(f"❌ Missing chapters: {sorted(missing_chapters)}")
        if extra_chapters:
            print(f"⚠️  Extra chapters: {sorted(extra_chapters)}")
        if not missing_chapters and not extra_chapters:
            print("✓ All chapters detected correctly")
        
        print()
        
        # Calculate total verses
        total_expected = sum(EXPECTED_STRUCTURE.values())
        total_found = 0
        
        for chapter, verses in self.verse_data.items():
            expanded = set()
            for v in verses:
                if '-' in v:
                    try:
                        start, end = map(int, v.split('-'))
                        for i in range(start, end + 1):
                            expanded.add(i)
                    except:
                        pass
                else:
                    try:
                        expanded.add(int(v))
                    except:
                        pass
            total_found += len(expanded)
        
        print(f"Expected total verses: {total_expected}")
        print(f"Found total verses: {total_found}")
        print(f"Gap: {total_expected - total_found}\n")
        
    def _generate_recommendations(self):
        """Generate actionable recommendations"""
        print("💡 RECOMMENDATIONS")
        print("-" * 80)
        
        print("1. Use the chapter_map above to create a file-to-chapter mapping")
        print("2. Process files in order, using the detected chapter for each file")
        print("3. Expand verse ranges (e.g., '1-2' -> ['1', '2'])")
        print("4. Validate final count matches 700 verses")
        print("\n" + "=" * 80)

def main():
    if len(sys.argv) < 2:
        epub_path = os.path.join(os.path.dirname(__file__), '..', '..', 'epub', 
                                  'Bhagavad-Gita As It Is (Original 1972 Edition).epub')
    else:
        epub_path = sys.argv[1]
    
    if not os.path.exists(epub_path):
        print(f"Error: EPUB not found at {epub_path}")
        sys.exit(1)
    
    analyzer = EPUBAnalyzer(epub_path)
    analyzer.analyze()

if __name__ == "__main__":
    main()
