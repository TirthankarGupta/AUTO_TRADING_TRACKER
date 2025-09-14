from pathlib import Path
p = Path("trading_journal.py")
s = p.read_text(encoding="utf-8")

start_token = "css = \"\"\""
i = s.find(start_token)
if i == -1:
    print("ERROR: css start token not found. Aborting.")
    raise SystemExit(1)

# find the closing </style> (we will insert BEFORE it)
end_style = s.find("</style>", i)
if end_style == -1:
    print("ERROR: </style> not found in css block. Aborting.")
    raise SystemExit(1)

# Layout CSS: move main content right to clear the sidebar + comfortable gap
# and make the journal table use more width (max width calc)
injection = r'''
/* === Layout nudges: move main content right, widen journal table === */
.block-container, .reportview-container .main .block-container, .main .block-container {
  margin-left: calc(300px + 28px) !important; /* sidebar width (300) + gap (28) */
  padding-left: 16px !important;
  padding-right: 16px !important;
}

/* Force main content area max-width to use space (avoid overly narrow containers) */
.reportview-container .main, .main {
  max-width: none !important;
}

/* Make the Trading Journal table wider while keeping padding */
.journal-table { width: calc(100% - 0px) !important; table-layout: fixed !important; }
.journal-table td { word-wrap: break-word; }

/* Make plots / plotly container expand nicely */
.stPlotlyChart > div, .element-container > .stPlotlyChart, .stPlotlyChart { width: 100% !important; }

/* Keep the hero fixed and unaffected */
.hero { z-index: 1500 !important; }
'''
# insert before </style>
new_s = s[:end_style] + injection + s[end_style:]
p.write_text(new_s, encoding="utf-8")
print("SUCCESS: injected layout CSS (content margin + wider journal table).")