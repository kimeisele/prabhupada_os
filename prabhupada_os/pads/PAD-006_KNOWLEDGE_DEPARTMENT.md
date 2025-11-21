# PAD-006: Knowledge Department (The Vedabase)

**STATUS: DRAFT v1.0**
**LAYER: PAD-6 (Knowledge)**
**DEPENDENCIES: PAD-5 (Runtime Kernel)**

---

## 1. The Vision: "Digital Shastra"

The Knowledge Department is the custodian of the absolute truth. Its mandate is simple but uncompromising: **100% Data Integrity.**

In the context of PrabhupadaOS, this means:
1.  **Ingestion**: Extracting verses from the EPUB with zero loss (700/700).
2.  **Storage**: Preserving the structure (Sanskrit, Synonyms, Translation, Purport).
3.  **Access**: Serving this knowledge to the Steward (PAD-7) and Interfaces (PAD-8).

## 2. The Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  KNOWLEDGE DEPARTMENT (PAD-6)               │
│                                                             │
│  ┌──────────────────────┐       ┌──────────────────────┐   │
│  │   INGESTION ENGINE   │──────▶│    THE VEDABASE      │   │
│  │ (import_gita.py)     │       │   (vedabase.db)      │   │
│  └──────────▲───────────┘       └──────────┬───────────┘   │
│             │                              │               │
│             │ (Reads)                      │ (Serves)      │
│             │                              ▼               │
│  ┌──────────────────────┐       ┌──────────────────────┐   │
│  │    SOURCE TEXTS      │       │   QUERY INTERFACE    │   │
│  │   (EPUB Files)       │       │ (SQL / Semantic)     │   │
│  └──────────────────────┘       └──────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 3. The "Law" of Ingestion

This section defines the **logic** that the code MUST implement. This is the source of truth.

### 3.1. The Source of Truth (The EPUB)
*   The source is `Bhagavad-Gita As It Is (Original 1972 Edition).epub`.
*   It is a collection of HTML files (`part00XX.html`).
*   **CRITICAL REALITY**: The EPUB structure is inconsistent.
    *   Some files contain one chapter.
    *   Some files contain *multiple* chapters (e.g., Ch 11 & 18 in `part0035.html`).
    *   Some files contain *fragments* of chapters.
    *   Chapter headers ("CHAPTER X") are unreliable markers for verse assignment if not handled statefully.

### 3.2. The State Machine (The Parser)
To handle the inconsistent structure, the parser MUST operate as a **State Machine**:

1.  **State**: `CurrentChapter` (Integer).
2.  **Triggers**:
    *   **Chapter Header**: `<h2 class="chapter-title">CHAPTER X</h2>` -> Updates `CurrentChapter`.
    *   **Verse Start**: `<div class="verse-trs4">` (Sanskrit) or `<div class="data-trs">` (Translation).
3.  **The Golden Rule of Assignment**:
    *   A verse belongs to the `CurrentChapter` active *at the moment the verse translation starts*.
    *   **EXCEPTION**: If a file contains multiple chapters, the parser must detect the chapter change *before* processing the next verse.
    *   **FALLBACK**: If no chapter header is seen, use the `FileMap` (hardcoded knowledge of which file starts with which chapter).

### 3.3. The File Map (The Territory)
The code must explicitly map files to their starting chapters to handle edge cases where headers are missing or ambiguous.

| File | Primary Chapter | Notes |
|------|-----------------|-------|
| `part0013.html` | 1 | |
| `part0014.html` | 2 | Contains most of Ch 2 |
| ... | ... | ... |
| `part0033.html` | 16 | Contains Ch 16 + Ch 18 fragments |
| `part0035.html` | 11 | Contains Ch 11 + Ch 18 fragments |

**Correction Directive (The Fix):**
*   **Chapter 2 Issue**: Verify if `part0014.html` is the *only* file for Chapter 2. If verses are missing, check `part0013.html` (end) or `part0015.html` (start).
*   **Chapter 10 Issue**: If Chapter 10 has *extra* verses, it means the parser is failing to switch state *out* of Chapter 10 when it enters Chapter 11. Check `part0026.html` (Ch 11 title page) - does it trigger the state change?

## 4. The Schema (vedabase.db)

The database is the immutable store.

```sql
CREATE TABLE verses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_code TEXT DEFAULT 'BG',  -- 'BG' for Bhagavad-gita
    chapter INTEGER NOT NULL,
    verse TEXT NOT NULL,          -- '1', '2-3' (ranges allowed)
    sanskrit TEXT,                -- Devanagari/Romanized
    synonyms TEXT,                -- Word-for-word meanings
    translation TEXT NOT NULL,    -- English translation
    purport TEXT,                 -- The commentary
    content_hash TEXT UNIQUE      -- For integrity verification
);

-- Full-Text Search Index (PAD-7 Requirement)
CREATE VIRTUAL TABLE verses_fts USING fts5(
    book_code, chapter, verse, 
    sanskrit, translation, purport
);
```

## 5. Verification Standards

1.  **Total Count**: Must be exactly **700** verses.
2.  **Chapter Counts**: Must match the canonical counts:
    *   Ch 1: 46 | Ch 2: 72 | Ch 3: 43 | Ch 4: 42 | Ch 5: 29 | Ch 6: 47
    *   Ch 7: 30 | Ch 8: 28 | Ch 9: 34 | Ch 10: 42 | Ch 11: 55 | Ch 12: 20
    *   Ch 13: 35 | Ch 14: 27 | Ch 15: 20 | Ch 16: 24 | Ch 17: 28 | Ch 18: 78
3.  **Integrity Check**: `SELECT COUNT(*) FROM verses` must equal 700.

---

## 6. Implementation Plan (The "Operation 700")

To achieve the vision of this PAD, the following steps must be executed in `prabhupada_os/knowledge/ingestion/import_gita.py`:

1.  **Audit the File Map**: Ensure EVERY `part*.html` file containing a `data-trs` div is in the map.
2.  **Fix State Transitions**:
    *   Ensure "CHAPTER ELEVEN" in `part0026.html` correctly switches state to 11.
    *   Ensure "CHAPTER TWO" in `part0014.html` is detected.
3.  **Re-run Import**: Execute the pipeline.
4.  **Verify**: Run `find_missing.py`.

**This PAD is the law. The code is the enforcement.**
