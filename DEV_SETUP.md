# DEV_SETUP

Project folder:
C:\Users\TIRTHANKAR\Documents\AUTO_TRADING_TRACKER

Quick environment setup (first time on a machine):
1. Open PowerShell and go to project folder:
   cd C:\Users\TIRTHANKAR\Documents\AUTO_TRADING_TRACKER

2. Create & activate venv (only first time):
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   If PowerShell blocks activation, run:
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

3. Install dependencies:
   pip install --upgrade pip
   pip install -r requirements.txt

4. When updating dependencies:
   pip freeze > requirements.txt
   git add requirements.txt
   git commit -m "Update requirements"
   git push

Useful commands:
- Run Streamlit UI: streamlit run trading_journal.py
- Quick test: python trading_journal.py  # prints Export complete! if test block present

Notes:
- Exports are saved to the `exports/` folder (ignored by git).
- Keep secrets (API keys) out of repo — use environment variables or .env (and add .env to .gitignore).
