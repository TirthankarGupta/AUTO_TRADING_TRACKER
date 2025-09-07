# NEXT_STEPS (short-term)

CURRENT_TASK:
✅ Add Streamlit export button into trading_journal.py  
➡️ Next: Replace sample dataframe with actual trading journal data (from CSV or database)  
➡️ Future: Add "Export filtered by date" UI  

---

When you return, follow this order:

1. Activate environment:
   .\.venv\Scripts\Activate.ps1

2. Quick smoke test:
   python trading_journal.py
   # Should print "Export complete!" if the test block exists.

3. Run Streamlit UI:
   streamlit run trading_journal.py
   # Open http://localhost:8501

4. Work on CURRENT_TASK. After each small change:
   git add .
   git commit -m "Concise message about change"
   git push

---

If git shows conflicts when pushing:
- Run: git pull --rebase origin main
- Resolve conflicts manually in the listed files
- git add <file(s)>
- git rebase --continue
- git push

---

Where key files live:
- trading_journal.py — main script (Streamlit UI + export)
- requirements.txt — dependencies
- exports/ — local export files (ignored by git)
- .gitignore — ignored files

---

⏸ If interrupted, update this file's CURRENT_TASK with the next tiny step to resume quickly.
