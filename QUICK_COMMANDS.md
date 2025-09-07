# QUICK_COMMANDS

# From project root (C:\Users\TIRTHANKAR\Documents\AUTO_TRADING_TRACKER)

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run smoke test (local)
python trading_journal.py

# Run Streamlit UI
streamlit run trading_journal.py

# Git: common quick flow
git status
git add .
git commit -m "Short message"
git pull --rebase origin main
git push -u origin main

# Untrack previously committed exports after updating .gitignore:
git rm -r --cached exports
git add .gitignore
git commit -m "Ignore exports folder"
git push

# Abort rebase if needed:
git rebase --abort
