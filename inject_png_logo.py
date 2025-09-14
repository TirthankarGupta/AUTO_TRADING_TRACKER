from pathlib import Path
import base64, glob, os, shutil, datetime
p = Path("trading_journal.py")
if not p.exists():
    print("ERROR: trading_journal.py not found in current folder. Aborting.")
    raise SystemExit(1)

# backup
bak_name = f"trading_journal_png_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
shutil.copy2(p, bak_name)
print(f"Backup saved as: {bak_name}")

s = p.read_text(encoding="utf-8")

insert_after = "hero_html ="
idx = s.find(insert_after)
if idx == -1:
    print("ERROR: Could not find 'hero_html =' marker. Aborting.")
    raise SystemExit(1)

# the block to insert (safe, overrides LOGO_DATA_URI if PNG found)
insertion = r'''
# --- PNG logo loader (auto): tries common names then any PNG in repo root ---
import os, base64, glob
_png_candidates = ["header_logo.png", "logo.png", "logo-header.png"] + sorted(glob.glob("*.png"))
_LOGO_PATH = None
for _p in _png_candidates:
    if _p and os.path.exists(_p):
        _LOGO_PATH = _p
        break
if _LOGO_PATH:
    try:
        with open(_LOGO_PATH, "rb") as _f:
            _b = base64.b64encode(_f.read()).decode("ascii")
        LOGO_DATA_URI = "data:image/png;base64," + _b
        print(f"INFO: Using PNG logo: {_LOGO_PATH}")
    except Exception as _e:
        print("WARNING: failed to load PNG logo:", _e)
# --- end PNG logo loader ---
'''

# insert the block right before hero_html definition
new_s = s[:idx] + insertion + s[idx:]
p.write_text(new_s, encoding="utf-8")
print("SUCCESS: insertion complete. Please restart Streamlit to see changes.")