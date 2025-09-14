from pathlib import Path
p = Path("trading_journal.py")
if not p.exists():
    print("ERROR: trading_journal.py not found in current folder. Aborting.")
    raise SystemExit(1)
s = p.read_text(encoding="utf-8")

start_marker = "/* === ALIGNMENT FIX BY AI === */"
end_marker = "/* end alignment fix */"

override_css = r"""
/* === ALIGNMENT FIX BY AI === */
/* Align block-container (chart/journal/pnl) with hero left edge and clamp widths */
:root {
  --sidebar-w: 300px;
  --hero-left-gap: 24px;
  --hero-top: 16px;
  --hero-height: 96px;
  --hero-padding: 12px;
}

/* Ensure hero is left-aligned and won't center its content */
.hero {
  left: calc(var(--sidebar-w) + var(--hero-left-gap)) !important;
  right: var(--hero-left-gap) !important;
  width: auto !important;
  margin: 0 !important;
  display: flex !important;
  justify-content: flex-start !important;
  align-items: center !important;
  gap: 18px !important;
  padding: 12px 18px !important;
  box-sizing: border-box !important;
}

/* Keep logo fixed size and prevent it pushing layout */
.hero-logo { flex: 0 0 96px !important; display:flex !important; align-items:center !important; justify-content:center !important; }
.hero-logo img { height: 72px !important; width: auto !important; max-width: 100% !important; object-fit: contain !important; }

/* Make main content align to the same left as hero */
.block-container, .reportview-container .main .block-container, .main .block-container {
  margin-left: calc(var(--sidebar-w) + var(--hero-left-gap)) !important;
  margin-right: var(--hero-left-gap) !important;
  padding-top: calc(var(--hero-top) + var(--hero-height) + 12px) !important; /* leave space for fixed hero */
  max-width: calc(100% - (var(--sidebar-w) + 2 * var(--hero-left-gap))) !important;
  box-sizing: border-box !important;
}

/* Ensure the PnL/top row uses same left alignment and width */
.block-container > div:first-child, .stBlock {
  margin-left: 0 !important;
  width: 100% !important;
}

/* Make plotly charts and dataframes use full available width inside block-container */
.stPlotlyChart, .stDataFrame, .journal-table {
  width: 100% !important;
  margin-left: 0 !important;
}

/* Prevent inner content from adding extra left padding */
.main .block-container > * { padding-left: 0 !important; box-sizing: border-box !important; }

/* Safety clamp: no overflow shifting */
html, body, .stApp { overflow-x: hidden !important; }

/* end alignment fix */
"""
# If marker exists, replace existing block between markers. Otherwise insert before </style>
if start_marker in s and end_marker in s:
    i = s.find(start_marker)
    j = s.find(end_marker, i)
    if j == -1:
        print("ERROR: start marker found but end marker missing. Aborting.")
        raise SystemExit(1)
    new_s = s[:i] + override_css + s[j + len(end_marker):]
else:
    insert_at = s.find("</style>")
    if insert_at == -1:
        print("ERROR: </style> not found. Aborting.")
        raise SystemExit(1)
    new_s = s[:insert_at] + override_css + s[insert_at:]

p.write_text(new_s, encoding="utf-8")
print("SUCCESS: alignment CSS injected (or replaced).")