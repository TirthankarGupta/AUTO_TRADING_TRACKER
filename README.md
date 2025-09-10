# ðŸ”´ CURRENT_TASK  
**Last Progress Log:** _
**Add Streamlit export button into trading_journal.py**  
âž¡ï¸ Next: Replace sample dataframe with real trading journal data  
âž¡ï¸ Future: Add "Export filtered by date" UI  

---
ï»¿# ðŸ”´ CURRENT_TASK  
**Add Streamlit export button into `trading_journal.py`**  
âž¡ï¸ Next: Replace sample dataframe with real trading journal data  
âž¡ï¸ Future: Add "Export filtered by date" UI  

---

# AUTO\_TRADING\_TRACKER

A Python-based **Trading Journal \& Dashboard** built for active traders.
Designed to track **options trades**, record every entry and exit, calculate **PnL**, and provide insights into performance over time.

Trading without journaling is like driving without a dashboard â€“ this tool helps you stay disciplined, learn from mistakes, and grow consistently.

## ðŸš€ Features

* ðŸ“Š **Trade Journal**: Record **entry/exit times, symbol, strike, quantity, and prices**.
* âœ… **PnL Tracking**: Auto-calculates **per-trade profit/loss** and **cumulative balance**.
* â±ï¸ **Time Tracking**: Capture **exact timestamps** of trade entry and exit.
* ðŸ—‚ï¸ **Backup Support**: Keeps backup copies of trading logs.
* ðŸ”” **Signals (Coming Soon)**: Real-time buy/sell signals \& alerts integrated with broker feed.
* ðŸ“Š **Dashboard (Planned)**: Interactive Streamlit dashboard with trade charts, win/loss ratios, and equity curve.

## ðŸ“‚ Project Structure

\\\\ash
AUTO\_TRADING\_TRACKER/
â”‚-- trading\_journal.py     # Core trading journal script
â”‚-- requirements.txt       # Dependencies
â”‚-- README.md              # Project documentation
â”‚-- .gitignore             # Git ignore rules
\\"
type README.md
Add-Content README.md @



\## ðŸ“‚ Project Structure



```bash

AUTO\_TRADING\_TRACKER/

â”‚-- trading\_journal.py     # Core trading journal script

â”‚-- requirements.txt       # Dependencies

â”‚-- README.md              # Project documentation

â”‚-- .gitignore             # Git ignore rules


## ðŸ“Š Example Trade Log

Hereâ€™s what a trade entry might look like:

| Date       | Symbol | Type | Entry Time | Entry Price | Exit Time | Exit Price | Qty | PnL   | Cumulative Balance |
|------------|--------|------|------------|-------------|-----------|------------|-----|-------|---------------------|
| 2025-09-07 | NIFTY  | CE   | 09:21 AM   | 152.50      | 09:47 AM  | 178.20     | 75  | â‚¹1,927 | â‚¹1,927              |
| 2025-09-07 | SENSEX | PE   | 11:05 AM   | 246.00      | 11:22 AM  | 219.80     | 75  | -â‚¹1,965 | -â‚¹38               |

âœ… Tracks **lot sizes**  
âœ… Auto-calculates **PnL per trade**  
âœ… Maintains **cumulative balance**

## âš™ï¸ Installation & Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/TirthankarGupta/AUTO_TRADING_TRACKER.git
   cd AUTO_TRADING_TRACKER
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Linux/Mac
   source venv/bin/activate
   # On Windows
   venv\Scripts\activate
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
4. Run the trading journal:
   ```bash
   python trading_journal.py


---

## ðŸ“ Notes
- This tool is intended for **personal trading journals** and backtesting.
- Works best when updated **daily** after trading sessions.
- Future versions will include:
  - ðŸ“Š Streamlit dashboard for live visualization
  - ðŸ”” Real-time broker-integrated signals
  - ðŸ“‚ Automated backups & export to Excel/CSV

---

## ðŸ¤ Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what youâ€™d like to improve.

---

## ðŸ“„ License
This project is licensed under the MIT License.

---

## ðŸ›  Developer Guide

For contributors (or when resuming after a break), see:

- [DEV_SETUP.md](DEV_SETUP.md) â†’ How to set up Python environment, install dependencies, and run the project  
- [NEXT_STEPS.md](NEXT_STEPS.md) â†’ The exact next tasks to continue development (kept updated)  
- [QUICK_COMMANDS.md](QUICK_COMMANDS.md) â†’ Common Git, Streamlit, and Python commands for quick reference  

These docs are kept in the repo to make onboarding and resuming work fast and easy.
