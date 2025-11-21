import zipfile
import sys
import os

def inspect_epub(epub_path):
    if not os.path.exists(epub_path):
        print(f"Error: File not found at {epub_path}")
        return

    try:
        with zipfile.ZipFile(epub_path, 'r') as z:
            print(f"--- Inspecting: {os.path.basename(epub_path)} ---")
            print("\n[File List]")
            file_list = z.namelist()
            for f in file_list:
                print(f" - {f}")

            # Heuristic to find Chapter 2
            # Looking for 'bg', '02', 'chap', etc.
            target_file = None
            
            # Prioritize files that look like "chapter 2"
            candidates = [f for f in file_list if '02' in f and ('html' in f or 'xhtml' in f)]
            
            if not candidates:
                 # Fallback: look for 'bg' and 'html'
                 candidates = [f for f in file_list if 'bg' in f and ('html' in f or 'xhtml' in f)]
            
            if candidates:
                # Pick the first one that seems most relevant. 
                # Often files are named like 'bg02.html' or 'chapter02.html'
                target_file = candidates[0]
                print(f"\n[Target Selected] Found candidate for Chapter 2: {target_file}")
            else:
                print("\n[Warning] Could not definitively identify Chapter 2. Dumping the first HTML file found.")
                html_files = [f for f in file_list if f.endswith('.html') or f.endswith('.xhtml')]
                if html_files:
                    target_file = html_files[0]
                    print(f"[Target Selected] Fallback to: {target_file}")
                else:
                    print("Error: No HTML/XHTML files found in EPUB.")
                    return

            print(f"\n--- Raw Content (First 500 lines of {target_file}) ---")
            with z.open(target_file) as f:
                content = f.read().decode('utf-8', errors='replace')
                lines = content.splitlines()
                for i, line in enumerate(lines[:500]):
                    print(f"{i+1}: {line}")

    except zipfile.BadZipFile:
        print("Error: Invalid EPUB file (not a valid ZIP).")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python epub_inspector.py <path_to_epub>")
        sys.exit(1)
    
    inspect_epub(sys.argv[1])
