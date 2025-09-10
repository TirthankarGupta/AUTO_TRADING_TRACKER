# save as find_bad_bytes.py in the same folder as trading_dashboard.py
fn = "trading_dashboard.py"
with open(fn, "rb") as f:
    data = f.read()
try:
    data.decode("utf-8")
    print("OK-utf8")
except UnicodeDecodeError as e:
    pos = e.start
    print(f"BADBYTE_POS:{pos}")
    start = max(0, pos-60)
    end = min(len(data), pos+60)
    context = data[start:end]
    # show context decoded as latin-1 so you can read the bytes
    print("CONTEXT_LATIN1:")
    print(context.decode("latin-1", errors="replace"))
