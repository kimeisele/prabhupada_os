# PrabhupadaOS

**Mission:** A Universal Intelligence Container for Vedic Knowledge.

## Architecture

PrabhupadaOS follows the "Intelligence Container" pattern:

1.  **The OS (Cortex)**: The System Prompt (`cortex/system.md`). It handles logic, intent, and ethics (Dharma).
2.  **The Hardware (Kernel)**: The Python Code (`kernel/bridge.py`). It is "dumb hardware" that handles I/O and Data Retrieval.

**Philosophy:**
- **Prompt = OS**: The intelligence is defined by the natural language instructions.
- **Code = Hardware**: The code is a deterministic substrate.
- **Zero Dependencies**: Runs on standard library Python.

## Quick Start

1.  **Initialize and Search**:
    The `bridge.py` script will automatically initialize the SQLite database with a sample verse (BG 2.13) on the first run.

    ```bash
    python kernel/bridge.py "soul"
    ```

2.  **Expected Output**:
    ```json
    {
      "status": "success",
      "count": 1,
      "data": [
        {
          "reference": "BG 2.13",
          "sanskrit": "...",
          "translation": "As the embodied soul continuously passes..."
        }
      ]
    }
    ```
