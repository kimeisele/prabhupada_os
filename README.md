# PrabhupadaOS
> "No Speculation. Clear Boundaries."

A deterministic, semantic operating system for the books of His Divine Grace A.C. Bhaktivedanta Swami Prabhupada.

## The "Cyborg Sage" Architecture

PrabhupadaOS is designed to be a **transparent interface** to an **immutable source of truth**. It strictly separates revealed knowledge (*Sruti*) from AI synthesis (*Smriti*).

### Core Components

1.  **The Kernel (`query_engine.py`)**: A Python-based semantic engine that implements the "No Speculation" protocol.
2.  **The Database (`vedabase.db`)**: A SQLite store containing exactly 700 canonical verses of the Bhagavad-gita As It Is (1972 Edition).
3.  **The Constitution (`CONSTITUTION.md`)**: The governing rules that prevent hallucination and ensure scientific rigor.

## The Protocol

Every query follows this strict pipeline:

1.  **Retrieval**: The OS searches `vedabase.db` for relevant verses.
2.  **Citation**: It returns the raw verses as the primary response ("Sruti").
3.  **Synthesis**: Only then does it allow AI to explain the context ("Smriti"), citing the specific verses.

## The AI-Native Architecture (GAD-000)

This system is designed to be operated by AI Agents (The Steward).

### For Human Directors
1.  **Boot the System**:
    ```bash
    python3 boot.py
    ```
2.  **Use the Library**:
    ```python
    import prabhupada
    prabhupada.ask("What is the soul?")
    ```

### For AI Operators
Refer to [AI_OPERATOR_MANUAL.md](AI_OPERATOR_MANUAL.md) for the GAD-000 compliant interface.

- **Status**: `python3 prabhupada_os/cli.py status --json`
- **Search**: `python3 prabhupada_os/cli.py search "query" --json`
- **Discover**: `python3 prabhupada_os/cli.py --help --json`

## Data Integrity
- **Verses**: 700 / 700 (100% Complete)
- **Source**: Bhagavad-gita As It Is (Original 1972 Edition)

- **Verses**: 700 / 700 (100% Complete)
- **Source**: Bhagavad-gita As It Is (Original 1972 Edition)
- **Format**: JSON-First API

## Legal Notice

This software is an interface. The content (texts of the Bhagavad-gita) is the property of the Bhaktivedanta Book Trust (BBT). This repository does not distribute the EPUB files directly. Users must provide their own legally obtained copies.
#### Features
- 📚 **The Vedabase**: SQLite database with 700 verses from Bhagavad-Gita As It Is (1972 Edition)
- 🤖 **The Steward**: Multi-tier chatbot with graceful degradation (Claude MCP → API → Local → SQLite FTS)
- 🏗️ **PAD Architecture**: Prabhupada Architecture Documents defining system structure
```bash
cd prabhupada_os

# Query the Vedabase
python3 interfaces/cli/chatbot_cli.py

# Import verses (requires EPUB - not included due to copyright)
python3 knowledge/ingestion/import_gita.py
```

#### Architecture
See `prabhupada_os/pads/` for detailed architecture documents:
- PAD-001: Runtime Department
- PAD-006: Knowledge Department (The Vedabase)

## Legal Notice

### Copyright & Fair Use
This repository contains **NO copyrighted materials**. The EPUB files and source texts are **excluded** via `.gitignore` and must be obtained separately.

The database schema and ingestion code are provided for **educational and research purposes** under Fair Use doctrine (17 U.S.C. § 107).

### Source Materials
To use this system, you must legally obtain:
- *Bhagavad-Gita As It Is* (Original 1972 Edition) by A.C. Bhaktivedanta Swami Prabhupada

Place EPUB files in `epub/` directory (gitignored).

## License
MIT License - See LICENSE file for details.

## Contributing
This is a personal research project. Feel free to fork and experiment!

---
*Built with 🙏 for spiritual knowledge preservation*
