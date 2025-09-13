from pathlib import Path
import shutil
import sys

def reencode(path):
    p = Path(path)
    if not p.exists():
        print("MISSING:", p)
        return 1
    bak = p.with_suffix(p.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(p, bak)
        print(f"Backup created: {bak}")
    # Read raw bytes and decode with a permissive fallback (latin-1),
    # then write back as UTF-8. This preserves bytes safely.
    raw = p.read_bytes()
    try:
        text = raw.decode("utf-8")
        print(f"{p}: already UTF-8 (no change).")
    except Exception:
        text = raw.decode("latin-1")
        p.write_text(text, encoding="utf-8")
        print(f"Re-encoded {p} -> UTF-8 (from latin-1 fallback).")
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reencode_file.py path/to/file")
        sys.exit(1)
    sys.exit(reencode(sys.argv[1]))
