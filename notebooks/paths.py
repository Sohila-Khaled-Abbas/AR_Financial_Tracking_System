"""
paths.py — Shared path configuration for all notebooks.
Import this at the top of any notebook to get correct project paths
without hardcoding OS-specific backslash strings.

Usage inside a notebook cell:
    from paths import RAW_DATA_DIR, OUTPUT_DIR, MAPPINGS_DIR
"""

from pathlib import Path

# notebooks/ is one level below the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── Data directories ──────────────────────────────────────────────────────────
RAW_DATA_DIR  = PROJECT_ROOT / "data" / "raw"
MAPPINGS_DIR  = PROJECT_ROOT / "data" / "mappings"
OUTPUT_DIR    = PROJECT_ROOT / "data" / "output"

# Auto-create output folder if it doesn't exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Quick sanity check ────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Project root : {PROJECT_ROOT}")
    print(f"Raw data     : {RAW_DATA_DIR}")
    print(f"Mappings     : {MAPPINGS_DIR}")
    print(f"Output       : {OUTPUT_DIR}")
