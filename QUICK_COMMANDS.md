# QUICK_COMMANDS

# from project root

# Activate venv
.\.venv\Scripts\Activate.ps1

# Install deps
pip install -r requirements.txt

# Run unit/smoke test (local)
python trading_journal.py

# Run Streamlit UI
streamlit run trading_journal.py

# Git common flow
git status
git add .
git commit -m "msg"
git pull --rebase origin main
git push -u origin main

# Update .gitignore and untrack previously tracked exports:
# (only if you change .gitignore to add new entries)
git rm -r --cached exports
git add .gitignore
git commit -m "Ignore exports folder"
git push

# If you need to abort an in-progress rebase:
git rebase --abort
