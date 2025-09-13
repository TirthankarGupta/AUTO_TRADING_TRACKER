# 🚀 Auto Trading Tracker

An experimental trading app built on **Angel One SmartAPI 2.0**.  
This project demonstrates my ability to integrate broker APIs, manage sessions securely, and build trading utilities (candlestick charts, indicators, and journaling).  

- **Immediate goal:**  
  Showcase candlesticks + indicators and maintain a real-time trading journal while placing trades manually in the Angel One app.  

- **Long-term vision:**  
  Evolve this tracker into a **full auto-trading bot** that executes trades automatically on my buy signals.  

---

## ✨ Features (current)
- ✅ **SmartAPI session manager** with secure TOTP login & auto-refresh (`smartapi_session_manager.py`).  
- ✅ **Trading bot integration** — `trading_bot.py` bootstraps session, validates tokens, runs smoke tests.  
- ✅ **Holdings fetch** — validated against live account.  
- ✅ **GitHub-ready project structure** — modular code, backups retained.  

---

## 📈 Features (planned / roadmap)
- 📊 Candlestick charting + indicators (EMA, momentum).  
- 📝 Automated journaling — trades captured from API (even if placed manually in Angel One).  
- 🔄 Resilient polling with retry + catch-up after internet outage.  
- ⚡ Real-time journaling via WebSocket feed.  
- 🤖 Auto-trading execution once strategies are proven stable.  

---

## 🛠️ Setup Instructions

### 1. Clone the repo
```bash
git clone https://github.com/TirthankarGupta/AUTO_TRADING_TRACKER.git
cd AUTO_TRADING_TRACKER
