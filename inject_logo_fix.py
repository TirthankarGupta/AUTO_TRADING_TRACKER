from pathlib import Path
p = Path("trading_journal.py")
s = p.read_text(encoding="utf-8")

start_token = "css = \"\"\""
i = s.find(start_token)
if i == -1:
    print("ERROR: css start token not found. Aborting.")
    raise SystemExit(1)
end = s.find('"""', i + len(start_token))
if end == -1:
    print("ERROR: css closing triple quotes not found. Aborting.")
    raise SystemExit(1)
insertion_point = end  # before the closing triple quotes

# CSS override for hero logo: ensure crisp, no white frame, correct size and alignment
override_css = r"""
/* === Logo override (surgical) === */
.hero-logo { flex: 0 0 96px !important; display:flex !important; align-items:center !important; justify-content:center !important; margin-left:4px !important; }
.hero-logo img {
  height: 72px !important;      /* target height */
  width: auto !important;
  display: block !important;
  border-radius: 8px !important;
  padding: 0 !important;
  margin: 0 !important;
  box-shadow: none !important;
  background: transparent !important; /* remove any white framing */
  border: none !important;
  image-rendering: -webkit-optimize-contrast !important;
  object-fit: contain !important;
}

/* Slight nudges to hero title to visually align with logo */
.hero { align-items: center !important; }
.hero-title .main { margin-top: 0 !important; }
"""

# Insert the override CSS right before the closing triple quotes of css block
new_s = s[:insertion_point] + override_css + s[insertion_point:]
p.write_text(new_s, encoding="utf-8")
print("SUCCESS: injected logo override CSS.")