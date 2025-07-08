// src/components/Navbar.js

import React, { useState, useEffect } from 'react';

const Navbar = ({ currentPage, setCurrentPage, user, onLogout }) => {
  const [marketStatus, setMarketStatus] = useState({ isOpen: false, text: '', color: 'gray', time: '' });
  const [showMobileMenu, setShowMobileMenu] = useState(false);

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

  const navLinks = [
    { key: 'live-dashboard', label: 'Dashboard' },
    { key: 'alerts', label: 'Alerts' },
    { key: 'plans', label: 'Trade Plans' },
    { key: 'journal', label: 'Journal' },
  ];

  return (
    <nav className="glass-navbar">
      <div className="navbar-container">
        {/* Brand */}
        <div className="navbar-brand gradient-text">SmartTrader</div>

        {/* Hamburger for mobile */}
        <button className="mobile-menu-btn" onClick={() => setShowMobileMenu(!showMobileMenu)}>
          <span className="hamburger" />
        </button>

        {/* Nav Links */}
        <div className={`navbar-links${showMobileMenu ? ' show' : ''}`}>
          {navLinks.map(link => (
            <button
              key={link.key}
              className={`btn nav-btn${currentPage === link.key ? ' active' : ''}`}
              onClick={() => {
                setCurrentPage(link.key);
                setShowMobileMenu(false);
              }}
            >
              {link.label}
            </button>
          ))}
        </div>

        {/* User/Market Status */}
        <div className="navbar-user-info">
          <div className="market-status">
            <span className={`market-dot ${marketStatus.color}`} />
            <span className="market-text">{marketStatus.text}</span>
            {marketStatus.time && <span className="market-time">{marketStatus.time}</span>}
          </div>
          {user ? (
            <div className="user-info">
              <span className="user-name">{user.first_name || user.username}</span>
              <button className="btn logout-btn" onClick={onLogout}>Logout</button>
            </div>
          ) : (
            <button className="btn login-btn" onClick={() => setCurrentPage('login')}>Login</button>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
