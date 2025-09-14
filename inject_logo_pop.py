from pathlib import Path
p = Path("trading_journal.py")
s = p.read_text(encoding="utf-8")

start_token = "css = \"\"\""
i = s.find(start_token)
if i == -1:
    print("ERROR: css start token not found. Aborting.")
    raise SystemExit(1)
# find closing </style> inside the css block
end_style = s.find("</style>", i)
if end_style == -1:
    print("ERROR: </style> not found inside css block. Aborting.")
    raise SystemExit(1)

# CSS override to make the logo visible (contrasting background + padding + shadow + brighten)
override = r'''
/* --- Logo visibility patch: subtle contrast, padding, shadow, brighten --- */
.hero-logo img {
  background: linear-gradient(135deg, rgba(16,90,75,0.14), rgba(7,45,52,0.08)) !important;
  padding: 10px !important;
  border-radius: 10px !important;
  box-shadow: 0 8px 20px rgba(7,18,28,0.35) !important;
  filter: brightness(1.18) saturate(1.06) !important;
  border: 1px solid rgba(255,255,255,0.02) !important;
  object-fit: contain !important;
}
'''
# insert the override right before the closing </style> tag
new_s = s[:end_style] + override + s[end_style:]
p.write_text(new_s, encoding="utf-8")
print("SUCCESS: injected logo-visibility override (inside CSS).")