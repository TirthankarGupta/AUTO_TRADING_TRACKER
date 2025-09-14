from pathlib import Path
p = Path("trading_journal.py")
s = p.read_text(encoding="utf-8")

start_token = "css = \"\"\""
i = s.find(start_token)
if i == -1:
    print("ERROR: css start token not found. Aborting.")
    raise SystemExit(1)
# find closing triple quotes after start_token
end = s.find('"""', i + len(start_token))
if end == -1:
    print("ERROR: css closing triple quotes not found. Aborting.")
    raise SystemExit(1)
endpos = end + 3

# NEW CLEAN CSS block (replace whole block)
new_css = r'''css = """
<style>
/* page background */
html, body, .stApp { background: #ffffff; margin:0; padding:0; }

/* hide Streamlit header & menu */
header[data-testid="stHeader"], #MainMenu, .css-1rs6os.edgvbvh3 { display: none !important; }

/* make the content container full-width and reserve top padding for the fixed hero */
.block-container, .reportview-container .main .block-container, .main .block-container {
  padding-left: 0 !important;
  padding-right: 0 !important;
  max-width: none !important;
  padding-top: 140px !important; /* reserve space for hero */
}

/* Sidebar sizes */
.stSidebar { background: #071a2a !important; padding-top: 12px !important; width: 300px !important; z-index: 2000 !important; }

/* Control header */
.control-header {
  color:#ffffff;
  font-weight:900;
  font-size:22px;
  padding:14px;
  background:#071a2a;
  border-radius:8px;
  text-align:center;
  text-transform:uppercase;
  border:1px solid rgba(255,255,255,0.04);
  margin-bottom:10px;
}

/* HERO: fixed at the top of viewport, starts after sidebar and stretches to right edge */
/* height: 96px, comfortable gap, high z-index */
.hero {
  position: fixed !important;
  top: 16px !important;
  left: calc(300px + 24px) !important; /* sidebar width + gap */
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

/* Hero logo */
.hero-logo { flex: 0 0 96px; display:flex; align-items:center; justify-content:center; margin-left:4px; }
.hero-logo img { height: 80px; width:auto; border-radius:6px; display:block; background:transparent; padding:0; margin:0; box-shadow:none; }

/* hero title */
.hero-title { display:flex; flex-direction:column; }
.hero-title .main { font-size:22px; font-weight:800; line-height:1.05; }
.hero-title .sub { margin-top:6px; font-size:12px; color:#cfe9ff; }

/* Sidebar default text color (white) */
.stSidebar * { color: #ffffff !important; }

/* Make sidebar input backgrounds white and visible text black */
.stSidebar input, .stSidebar select, .stSidebar textarea, .stSidebar .stButton>button, .stSidebar .stDownloadButton>button {
  background: #ffffff !important;
  color: #000000 !important;
  border-radius:6px !important;
}

/* FORCE selectbox displayed text and dropdown items to black (broad safe selectors) */
/* covers role="combobox", baseweb selects, select elements and nested spans */
.stSidebar div[role="combobox"], .stSidebar .stSelectbox, .stSidebar .stSelectbox *, 
.stSidebar select, .stSidebar select *, .stSidebar [data-baseweb="select"] * , .stSidebar [data-testid="stSelectbox"] * {
  color: #000000 !important;
  -webkit-text-fill-color: #000000 !important;
  opacity: 1 !important;
}

/* Force select option styling (when dropdown opens) */
.stSidebar option, .stSidebar select option {
  color: #000000 !important;
  background: #ffffff !important;
}

/* Force button labels and nested spans to black */
.stSidebar .stButton>button, .stSidebar .stButton>button *, .stSidebar button, .stSidebar button * {
  color: #000000 !important;
  -webkit-text-fill-color: #000000 !important;
  opacity: 1 !important;
}

/* Ensure placeholders visible */
.stSidebar ::placeholder { color: #000000 !important; opacity: 1 !important; -webkit-text-fill-color: #000000 !important; }

/* Journal table */
.journal-title { margin-top:8px; margin-bottom:6px; font-size:16px; font-weight:700; }
.journal-table th { text-transform: capitalize; background:#f7fafc; padding:8px; text-align:left; font-weight:700; }
.journal-table tr:nth-child(even) { background:#fbfbfb; }

/* Responsive fallbacks: hero becomes relative on narrow screens */
@media (max-width: 1100px) {
  .hero {
    position: relative !important;
    left: 0 !important;
    right: 0 !important;
    width: calc(100% - 40px) !important;
    margin: 12px 20px !important;
    height: auto !important;
  }
  .block-container, .reportview-container .main .block-container, .main .block-container {
    padding-top: 18px !important;
  }
}
</style>
"""'''

# replace css block only
s2 = s[:i] + new_css + s[endpos:]
p.write_text(s2, encoding="utf-8")
print("SUCCESS: CSS block replaced (fixed hero + forced sidebar text colors).")