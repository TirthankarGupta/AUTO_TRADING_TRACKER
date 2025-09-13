import streamlit as st
import ast, importlib, traceback, pathlib

st.set_page_config(page_title='Import Diagnostic', layout='wide')
st.title('Trading Dashboard — Import Diagnostic')

p = pathlib.Path('trading_dashboard.py')
if not p.exists():
    st.error('trading_dashboard.py not found in current folder: ' + str(p.resolve()))
    st.stop()

code = p.read_text(encoding='utf8')

# parse imports from file (no execution)
try:
    tree = ast.parse(code, filename=str(p))
except Exception as e:
    st.error('Failed to parse trading_dashboard.py: ' + repr(e))
    st.code(code[:4000])
    raise

imports = []
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for n in node.names:
            imports.append(n.name.split('.')[0])
    elif isinstance(node, ast.ImportFrom):
        if node.module is not None:
            imports.append(node.module.split('.')[0])

# unique, preserve order
seen = set()
mods = []
for m in imports:
    if m not in seen:
        seen.add(m)
        mods.append(m)

st.write('Found the following top-level modules to test import:')
st.write(mods)

results = []
for mod in mods:
    st.write('---')
    st.write(f'Attempting import {mod} ...')
    try:
        imported = importlib.import_module(mod)
        ver = getattr(imported, "__version__", "<no __version__>")
        st.success(f'OK: imported {mod} (version={ver})')
        results.append((mod, True, None))
    except Exception as exc:
        tb = traceback.format_exc()
        st.error(f'FAILED: import {mod}')
        st.code(tb)
        results.append((mod, False, tb))

# Summary
fails = [r for r in results if not r[1]]
st.header('Summary')
st.write(f'Total modules tested: {len(results)}')
st.write(f'Failures: {len(fails)}')
if fails:
    st.write('Failed modules (first 10):')
    for m, ok, tb in fails[:10]:
        st.write('-', m)
    st.warning('Fix the failed imports (install missing packages, or correct module names) then re-run your dashboard.')
else:
    st.success('All top-level imports succeeded. The problem may be runtime code after imports (data loads, blocking calls).')
