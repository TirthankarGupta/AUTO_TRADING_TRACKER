from pathlib import Path
p = Path("trading_journal.py")
s = p.read_text(encoding="utf-8")

start_token = 'css = """'
i = s.find(start_token)
if i == -1:
    print("ERROR: css start token not found. Aborting.")
    raise SystemExit(1)
end = s.find('"""', i + len(start_token))
if end == -1:
    print("ERROR: css closing triple quotes not found. Aborting.")
    raise SystemExit(1)

# BROAD CSS to force visible text inside sidebar inputs/selects/buttons
inject_css = r"""
/* === FORCED SIDEBAR TEXT COLORS - broad coverage === */
.stSidebar input, .stSidebar input *, .stSidebar input::placeholder,
.stSidebar textarea, .stSidebar textarea *, 
.stSidebar select, .stSidebar select *, 
.stSidebar .stSelectbox, .stSidebar .stSelectbox *,
.stSidebar div[role="combobox"], .stSidebar div[role="combobox"] *,
.stSidebar [data-baseweb="select"] *, .stSidebar [data-testid="stSelectbox"] * {
  color: #000000 !important;
  -webkit-text-fill-color: #000000 !important;
  opacity: 1 !important;
}

.stSidebar option, .stSidebar select option {
  color: #000000 !important;
  background: #ffffff !important;
}

.stSidebar .stButton>button, .stSidebar .stButton>button *,
.stSidebar button, .stSidebar button * {
  color: #000000 !important;
  -webkit-text-fill-color: #000000 !important;
  opacity: 1 !important;
}

.stSidebar ::placeholder {
  color: #000000 !important;
  opacity: 1 !important;
  -webkit-text-fill-color: #000000 !important;
}
"""
new_s = s[:end] + inject_css + s[end:]
p.write_text(new_s, encoding="utf-8")
print("SUCCESS: injected BROAD sidebar CSS to force input/select/button text to black.")