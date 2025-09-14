from pathlib import Path
p = Path("trading_journal.py")
if not p.exists():
    print("ERROR: trading_journal.py not found. Aborting.")
    raise SystemExit(1)
s = p.read_text(encoding="utf-8")

# find closing </style> inside css block and insert overrides just before it
insert_pos = s.find("</style>")
if insert_pos == -1:
    print("ERROR: </style> not found. Aborting.")
    raise SystemExit(1)

override_css = r"""
/* ==== HERO / LOGO FIX (injected override) ==== */
/* Ensure hero is a left-aligned flex container and logo is clamped */
.hero {
  position: fixed !important;
  top: 16px !important;
  left: calc(300px + 24px) !important;
  right: 24px !important;
  height: 96px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important; /* keep content left */
  gap: 18px !important;
  padding: 12px 18px !important;
  overflow: visible !important;
  z-index: 1600 !important;
}

/* Logo container keeps fixed width and centers the image */
.hero-logo {
  flex: 0 0 96px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  margin-right: 12px !important;
  background: transparent !important;
}

/* Clamp image size and ensure it won't expand the hero */
.hero-logo img {
  height: 72px !important;
  width: auto !important;
  max-width: 100% !important;
  object-fit: contain !important;
  border-radius: 8px !important;
  box-shadow: none !important;
  display: block !important;
}

/* Keep title left-aligned and vertically centered */
.hero-title { display:flex !important; flex-direction:column !important; align-items:flex-start !important; }
.hero-title .main { font-size:22px !important; font-weight:800 !important; line-height:1.05 !important; text-align:left !important; }
.hero-title .sub { font-size:12px !important; color:#cfe9ff !important; text-align:left !important; margin-top:6px !important; }

/* small defensive rule: prevent hero internal elements from wrapping badly */
.hero > * { min-width: 0 !important; }

/* end hero override */
"""
new_s = s[:insert_pos] + override_css + s[insert_pos:]
p.write_text(new_s, encoding="utf-8")
print("SUCCESS: header CSS override injected before </style>.")