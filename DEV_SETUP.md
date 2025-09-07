# DEV_SETUP

Project folder:
`C:\Users\TIRTHANKAR\Documents\AUTO_TRADING_TRACKER`

Quick environment setup (first time on a machine):
1. Open PowerShell and cd to project folder:
   cd C:\Users\TIRTHANKAR\Documents\AUTO_TRADING_TRACKER

2. Create & activate venv:
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

3. Install dependencies:
   pip install --upgrade pip
   pip install -r requirements.txt

4. If you change requirements.txt:
   pip freeze > requirements.txt
   git add requirements.txt
   git commit -m "Update requirements"
   git push

Notes:
- Exports are saved to `exports/` (ignored by git). Local CSV/XLSX will remain on disk.
- Streamlit UI: `streamlit run trading_journal.py`
- If PowerShell blocks activation: run
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
