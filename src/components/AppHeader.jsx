import React from 'react';
import '../styles/header.css';

export default function AppHeader({ logoSrc, title = 'AUTO TRADING TRACKER', showControlPanel = true }) {
  return (
    <header className="att-header">
      <div className="att-header-inner">
        <div className="att-left">
          <img src={logoSrc} alt="app-logo" className="att-logo" />
          <div className="att-title">
            <span className="att-title-main">{title}</span>
            <span className="att-title-sub">Connected</span>
          </div>
        </div>

        {showControlPanel && (
          <nav className="att-control" aria-label="control-panel">
            <button className="att-btn">Start</button>
            <button className="att-btn">Stop</button>
            <div className="att-status">Status: <strong>Idle</strong></div>
          </nav>
        )}
      </div>
      <div className="att-sep" />
    </header>
  );
}
