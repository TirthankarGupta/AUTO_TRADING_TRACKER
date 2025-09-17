# QUICK COMMANDS — AUTO TRADING TRACKER

## 1. Navigate to project folder
```powershell
cd C:\AUTO_TRADING_TRACKER
```

## 2. Activate virtual environment
```powershell
.\.venv\Scripts\Activate
```

## 3. Run Streamlit app
```powershell
.\.venv\Scripts\python -m streamlit run trading_journal.py
```

## 4. Kill Streamlit server on port 8501
```powershell
netstat -ano | Select-String ":8501" | ForEach-Object { $_.ToString().Trim().Split()[-1] } | ForEach-Object { taskkill /PID $_ /F } 2>$null
```

## 5. Clear Streamlit cache
```powershell
.\.venv\Scripts\python -m streamlit cache clear
Copy code
```

## 6. Check Git repo status
```powershell
git status
```

## 7. Fetch all branches & tags
```powershell
git fetch --all --tags
```

## 8. Compare local file with final tag
```powershell
git diff v1.2-final -- trading_journal.py
```

## 9. Restore file from final tag
```powershell
git checkout v1.2-final -- trading_journal.py
```

## 10. Commit and push changes
```powershell
git add trading_journal.py
git commit -m "Update trading_journal.py"
git push origin HEAD
```

