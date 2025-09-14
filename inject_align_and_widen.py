from pathlib import Path
p = Path("trading_journal.py")
if not p.exists():
    print("ERROR: trading_journal.py not found. Aborting.")
    raise SystemExit(1)

# make a timestamped backup (extra safety)
import shutil, datetime
bak = f"trading_journal_align_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
shutil.copy2(p, bak)
print("Backup created:", bak)

s = p.read_text(encoding="utf-8")

# 1) Replace CSS block between css = """ and the closing """ that contains </style>
start_token = 'css = """'
i = s.find(start_token)
if i == -1:
    print("ERROR: css start token not found. Aborting.")
    raise SystemExit(1)

# find closing triple quotes after start
end = s.find('"""', i + len(start_token))
if end == -1:
    print("ERROR: css closing triple quotes not found. Aborting.")
    raise SystemExit(1)
endpos = end + 3

# New tuned CSS: aligns content with hero, widens journal and gives comments more room
new_css_block = r'''css = """
<style>
/* Canvas + remove Streamlit top chrome */
html, body, .stApp { background: #ffffff; margin:0; padding:0; }
header[data-testid="stHeader"], #MainMenu, .css-1rs6os.edgvbvh3 { display: none !important; }

/* Reserve space for the fixed hero header (hero height 96px + top margin) */
.block-container, .reportview-container .main .block-container, .main .block-container {
  padding-top: 140px !important; /* keep hero space */
  padding-left: 20px !important;
  padding-right: 20px !important;
  max-width: none !important;
}

/* Sidebar appearance */
.stSidebar { background: #071a2a !important; padding-top: 12px !important; width: 300px !important; z-index: 2000 !important; }

/* CONTROL header */
.control-header {
  color:#ffffff; font-weight:900; font-size:22px; padding:14px;
  background:#071a2a; border-radius:8px; text-align:center; text-transform:uppercase;
  border:1px solid rgba(255,255,255,0.04); margin-bottom:10px;
}

/* HERO - fixed and stretched (unchanged) */
.hero {
  position: fixed !important;
  top: 16px !important;
  left: calc(300px + 24px) !important; /* hero starts after sidebar + small gap */
  right: 24px !important;
  height: 96px !important;
  z-index: 1500 !important;
  border-radius:10px !important;
  box-shadow: 0 8px 22px rgba(7,18,28,0.10) !important;
  background: linear-gradient(90deg, #062033 0%, #071a2a 100%) !important;
  color:#ffffff !important;
  display:flex !important;
  align-items:center !important;
  gap:18px !important;
  padding:14px 18px !important;
  overflow:hidden !important;
}

/* Make main content align with hero left edge (chart + PnL row) */
.reportview-container .main, .main {
  margin-left: calc(300px + 24px) !important; /* align content with hero left */
  max-width: calc(100% - (300px + 48px)) !important;
}

/* Sidebar input readability */
.stSidebar * { color: #ffffff !important; }
.stSidebar input, .stSidebar select, .stSidebar textarea, .stSidebar .stButton>button, .stSidebar .stDownloadButton>button {
  background: #ffffff !important; color: #000000 !important; border-radius:6px !important;
}

/* Force selectbox + dropdown text to black broadly */
.stSidebar div[role="combobox"], .stSidebar .stSelectbox, .stSidebar .stSelectbox *, .stSidebar select, .stSidebar select * {
  color: #000000 !important;
  -webkit-text-fill-color: #000000 !important;
}

/* Increase Trading Journal width and make Comments column roomier */
.journal-table { width: 100% !important; table-layout: auto !important; }
.journal-table th, .journal-table td { padding: 10px 14px !important; vertical-align: middle !important; }
.journal-table td:nth-child(1) { width: 40px !important; }  /* No. */
.journal-table td:nth-child(2) { width: 180px !important; } /* Symbol */
.journal-table td:nth-child(3) { width: 160px !important; } /* Entry Time */
.journal-table td:nth-child(4) { width: 110px !important; } /* Entry Price */
.journal-table td:nth-child(5) { width: 160px !important; } /* Exit Time */
.journal-table td:nth-child(6) { width: 110px !important; } /* Exit Price */
.journal-table td:nth-child(7) { width: 32% !important; }   /* Comments larger area */
.journal-table td:nth-child(8) { width: 110px !important; } /* Gross PnL */

/* ensure plotly uses full width */
.stPlotlyChart > div, .element-container > .stPlotlyChart, .stPlotlyChart { width: 100% !important; }

/* small responsive fallback */
@media (max-width: 1200px) {
  .reportview-container .main, .main { margin-left: calc(300px + 16px) !important; }
  .journal-table td:nth-child(7) { width: auto !important; }
}
</style>
"""'''

# perform replacement
s2 = s[:i] + new_css_block + s[endpos:]
# 2) Replace 'Emas' heading with 'EMAs' (covers the exact st.markdown usage)
s2 = s2.replace("<h3 style='color:#ffffff;'>Emas</h3>", "<h3 style='color:#ffffff;'>EMAs</h3>")
s2 = s2.replace("st.markdown(\"<h3 style='color:#ffffff;'>Emas</h3>\"", "st.markdown(\"<h3 style='color:#ffffff;'>EMAs</h3>\"")  # safe attempt for alternate formatting

# write back
p.write_text(s2, encoding="utf-8")
print("SUCCESS: CSS replaced, 'Emas' -> 'EMAs' updated, backup:", bak)