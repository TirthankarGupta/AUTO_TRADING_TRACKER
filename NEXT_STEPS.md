# NEXT_STEPS (short-term)

When you return, follow this order to resume work quickly:

1. Activate environment
   .\.venv\Scripts\Activate.ps1

2. Run tests / quick smoke:
   python trading_journal.py
   # should print "Export complete!" when test block exists

3. Start Streamlit (to test UI)
   streamlit run trading_journal.py

4. Implement / test next feature (examples):
   - Wire dual_export into Streamlit (if not already)
   - Replace sample df with real journal load (CSV or Sheet1)
   - Add "Export filtered by date" UI
   - Integrate Angel One read-only feed (later)

5. Commit often:
   git add .
   git commit -m "Short message"
   git push

If a merge/push conflict occurs:
- Run git pull --rebase origin main
- Resolve conflicts in files, then:
  git add <files>
  git rebase --continue
  git push

Where files live:
- trading_journal.py — main script (Streamlit UI + export)
- requirements.txt — python packages
- exports/ — local exports (ignored)
- .gitignore — ignored files

If you are interrupted: write the exact next small task in this file under "CURRENT_TASK" to pick up later.
