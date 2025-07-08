// src/components/Navbar.js

import React, { useState, useEffect, useRef } from 'react';

const Navbar = ({ currentPage, setCurrentPage, user, onLogout }) => {
  const [marketStatus, setMarketStatus] = useState({ isOpen: false, text: '', color: 'gray', time: '' });
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const profileRef = useRef(null);

  useEffect(() => {
    const updateMarketStatus = () => {
      const now = new Date();
      const day = now.getDay();
      const open = new Date(now);
      open.setHours(9, 15, 0, 0);
      const close = new Date(now);
      close.setHours(15, 30, 0, 0);
      let isOpen = day >= 1 && day <= 5 && now >= open && now <= close;
      let text = isOpen ? 'Market Open' : 'Market Closed';
      let color = isOpen ? 'green' : 'red';
      let time = '';
      if (!isOpen) {
        // Show time until next open
        let nextOpen = new Date(now);
        if (now > close || day === 6) {
          // After close or Saturday, next open is next weekday
          nextOpen.setDate(now.getDate() + ((8 - day) % 7 || 1));
        }
        nextOpen.setHours(9, 15, 0, 0);
        const diff = nextOpen - now;
        if (diff > 0) {
          const hours = Math.floor(diff / 1000 / 60 / 60);
          const mins = Math.floor((diff / 1000 / 60) % 60);
          time = `Opens in ${hours}h ${mins}m`;
        }
      } else {
        // Show time until close
        const diff = close - now;
        const hours = Math.floor(diff / 1000 / 60 / 60);
        const mins = Math.floor((diff / 1000 / 60) % 60);
        time = `Closes in ${hours}h ${mins}m`;
      }
      setMarketStatus({ isOpen, text, color, time });
    };
    updateMarketStatus();
    const interval = setInterval(updateMarketStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function handleClickOutside(event) {
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setShowProfileDropdown(false);
      }
    }
    if (showProfileDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    } else {
      document.removeEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showProfileDropdown]);

  const navLinks = [
    { key: 'alerts', label: 'Alerts' },
    { key: 'virtual-trading', label: 'Virtual Trading' },
    { key: 'plans', label: 'Trade Plans' },
    { key: 'journal', label: 'Journal' },
  ];

  return (
    <nav className="glass-navbar" style={{ whiteSpace: 'nowrap' }}>
      <div className="navbar-main" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', flexWrap: 'nowrap' }}>
        <div className="navbar-brand gradient-text" style={{marginLeft: '2.5rem', marginRight: '2.5rem', whiteSpace: 'nowrap' }}>SmartTrader</div>
        <div className="navbar-links" style={{ gap: '2.2rem', display: 'flex', alignItems: 'center', flexShrink: 1, whiteSpace: 'nowrap' }}>
          {navLinks.map(link => (
            <button
              key={link.key}
              className={`btn nav-btn${currentPage === link.key ? ' active' : ''}`}
              onClick={() => setCurrentPage(link.key)}
              style={{ whiteSpace: 'nowrap' }}
            >
              {link.label}
            </button>
          ))}
        </div>
        <div className="navbar-user-info" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexShrink: 0, minWidth: 0 }}>
          <div className="navbar-market-status" style={{ marginRight: '1.2rem' }}>
            <span
              className="market-status-pill"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                padding: '0.35em 1.2em',
                borderRadius: '999px',
                fontWeight: 700,
                fontSize: '1.05em',
                background: marketStatus.isOpen
                  ? 'linear-gradient(90deg, #22c55e 0%, #3b82f6 100%)'
                  : 'linear-gradient(90deg, #ef4444 0%, #f59e42 100%)',
                color: '#fff',
                boxShadow: '0 2px 8px 0 rgba(0,0,0,0.10)',
                whiteSpace: 'nowrap',
                margin: 0,
              }}
            >
              {marketStatus.isOpen ? (
                <span style={{ fontSize: '1.2em', marginRight: 8 }}>🟢</span>
              ) : (
                <span style={{ fontSize: '1.2em', marginRight: 8 }}>⏳</span>
              )}
              {marketStatus.text}
              <span style={{ fontWeight: 400, marginLeft: 10, fontSize: '0.95em', opacity: 0.85 }}>
                {marketStatus.time}
              </span>
            </span>
          </div>
          {user ? (
            <div ref={profileRef} style={{marginRight: '2.5rem', position: 'relative', minWidth: 0 }}>
              <button
                className="profile-name-btn"
                onClick={() => setShowProfileDropdown(v => !v)}
                aria-haspopup="true"
                aria-expanded={showProfileDropdown}
              >
                {user.first_name || user.username}
               
              </button>
              {showProfileDropdown && (
                <div className="profile-dropdown" style={{ position: 'absolute', right: 0, top: '110%', background: '#181f2e', borderRadius: 8, boxShadow: '0 4px 16px 0 rgba(30,41,59,0.13)', zIndex: 10, minWidth: 120 }}>
                  <button className="btn logout-btn" style={{ width: '100%', textAlign: 'left', padding: '0.7em 1.2em', background: 'none', border: 'none', color: '#ef4444', fontWeight: 600, cursor: 'pointer', borderRadius: 8 }} onClick={onLogout}>
                    Logout
                  </button>
                </div>
              )}
            </div>
          ) : (
            <button className="btn login-btn" onClick={() => { window.location.href = '/api/auth/upstox/login/'; }}>Login</button>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
