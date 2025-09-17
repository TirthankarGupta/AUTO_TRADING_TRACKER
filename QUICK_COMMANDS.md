QUICK COMMANDS — AUTO TRADING TRACKER
1. Navigate to project folder
cd C:\AUTO_TRADING_TRACKER

2. Activate virtual environment
.\.venv\Scripts\Activate

3. Run Streamlit app
.\.venv\Scripts\python -m streamlit run trading_journal.py

4. Kill Streamlit server on port 8501
netstat -ano | Select-String ":8501" | ForEach-Object { $_.ToString().Trim().Split()[-1] } | ForEach-Object { taskkill /PID $_ /F } 2>$null

5. Clear Streamlit cache
.\.venv\Scripts\python -m streamlit cache clear

6. Check Git repo status
git status

7. Fetch all branches & tags
git fetch --all --tags

8. Compare local file with final tag
git diff v1.2-final -- trading_journal.py

9. Restore file from final tag
git checkout v1.2-final -- trading_journal.py

10. Commit and push changes
git add trading_journal.py
git commit -m "Update trading_journal.py"
git push origin HEAD