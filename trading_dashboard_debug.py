import traceback, sys, io, os

try:
    # Run the original script in its own globals (mimic running as __main__)
    globals_dict = {"__name__": "__main__", "__file__": os.path.abspath("trading_dashboard.py")}
    with open('trading_dashboard.py', 'r', encoding='utf8') as f:
        code = f.read()
    exec(compile(code, 'trading_dashboard.py', 'exec'), globals_dict)
except Exception:
    tb = traceback.format_exc()
    # Save full traceback for copying
    with open('trading_dashboard_error.log', 'w', encoding='utf8') as logf:
        logf.write(tb)
    print('
--- RUNTIME EXCEPTION (captured by wrapper) ---
')
    print(tb)
    raise
