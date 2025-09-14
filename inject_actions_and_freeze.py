from pathlib import Path
p = Path("trading_journal.py")
if not p.exists():
    print("ERROR: trading_journal.py not found. Aborting.")
    raise SystemExit(1)
s = p.read_text(encoding="utf-8")

insert_at = s.find("</style>")
if insert_at == -1:
    print("ERROR: </style> not found in trading_journal.py CSS block. Aborting.")
    raise SystemExit(1)

override = r"""
/* === Actions visibility & freeze-pane overrides (injected) === */
/* 1) Force sidebar button/input/dropdown text to black (broad catch-alls) */
.stSidebar .stButton>button,
.stSidebar .stButton>button * ,
.stSidebar button,
.stSidebar button * {
  color: #000000 !important;
  -webkit-text-fill-color: #000000 !important;
  opacity: 1 !important;
}

/* Force inputs / selects / placeholders to use black text in sidebar */
.stSidebar input[type="text"],
.stSidebar input[type="search"],
.stSidebar .stTextInput input,
.stSidebar textarea,
.stSidebar select,
.stSidebar .stSelectbox,
.stSidebar .stSelectbox * {
  color: #000000 !important;
  -webkit-text-fill-color: #000000 !important;
  opacity: 1 !important;
}
.stSidebar ::placeholder { color:#000000 !important; opacity:1 !important; }

/* Defensive: also target baseweb/select and other internal selectors */
.stSidebar [data-baseweb="select"] *, .stSidebar [data-testid="stSelectbox"] * { color: #000000 !important; }

/* 2) Freeze layout: fix sidebar + hero and make main content the scroll area */
/* lock horizontal overflow to avoid page shift */
html, body, .stApp { overflow-x: hidden !important; }

/* fix the sidebar so it does not scroll away */
.stSidebar {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  height: 100vh !important;
  overflow-y: auto !important;
  padding-top: 16px !important;
  z-index: 2000 !important;
}

/* ensure hero stays fixed at top (visible) */
.hero {
  position: fixed !important;
  top: 16px !important;
  left: calc(300px + 24px) !important; /* align right of sidebar */
  right: 24px !important;
  z-index: 1600 !important;
}

/* make the main block scrollable (content area) */
.block-container, .reportview-container .main .block-container, .main .block-container {
  margin-left: calc(300px + 24px) !important;
  margin-right: 24px !important;
  padding-top: 124px !important; /* leave space for the hero */
  height: calc(100vh - 140px) !important; /* viewport minus hero/padding */
  overflow-y: auto !important;
}

/* ensure charts/tables inside main can grow and use width */
.stPlotlyChart, .stDataFrame, .journal-table { width: 100% !important; }

/* small nicety: avoid unexpected horizontal scrollbar inside main */
.block-container * { max-width: 100% !important; box-sizing: border-box !important; }

/* end injected overrides */
"""
new_s = s[:insert_at] + override + s[insert_at:]
p.write_text(new_s, encoding="utf-8")
print("SUCCESS: injected Actions visibility + freeze-pane CSS overrides.")