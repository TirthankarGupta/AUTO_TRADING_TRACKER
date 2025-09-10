import glob, sys
def check(path):
    try:
        open(path,'r', encoding='utf-8').read()
        return None
    except Exception as e:
        return str(e)

exts = ('.py','.csv','.css','.html','.txt')
bad = []
for f in sorted(glob.glob('**/*', recursive=True)):
    if f.lower().endswith(exts):
        err = check(f)
        if err:
            bad.append((f, err))

if not bad:
    print("OK: no problems found (all checked files decode as UTF-8).")
else:
    for f,err in bad:
        print(f"{f} => {err}")
sys.exit(0)
