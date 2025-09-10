# fix_encoding.py
# Reads trading_dashboard.py as cp1252 (common Windows encoding),
# replaces common smart chars with ASCII, and writes UTF-8.

fn = "trading_dashboard.py"
bak = fn + ".fixed_backup"

import shutil
shutil.copy2(fn, bak)  # create another safety backup

with open(fn, "r", encoding="cp1252", errors="replace") as f:
    txt = f.read()

# replace common problematic CP1252 characters with safe ASCII
replacements = {
    "\u2018": "'",  # left single quote
    "\u2019": "'",  # right single quote
    "\u201c": '"',  # left double quote
    "\u201d": '"',  # right double quote
    "\u2013": "-",  # en-dash
    "\u2014": "-",  # em-dash
    "\u2026": "...",# ellipsis
    "\u00A0": " ",  # non-breaking space
    "\x97": "-",    # CP1252 em-dash byte (just in case)
}

for bad, good in replacements.items():
    txt = txt.replace(bad, good)

# (Optional) If you want to target the exact problematic fragment (pos 8317),
# we could print around it for inspection. But the above global replacements
# handle the common culprits.

with open(fn, "w", encoding="utf-8") as f:
    f.write(txt)

print("Re-saved trading_dashboard.py as UTF-8, backup:", bak)
