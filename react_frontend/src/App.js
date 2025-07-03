// src/App.js

import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import AlertsPage from './pages/AlertsPage';
import TradePlansPage from './pages/TradePlansPage';
import TradeJournalPage from './pages/TradeJournalPage';
import LoginCallback from './pages/LoginCallback'; // ✅ NEW: For handling login
import { getCurrentUser, logout } from './api/apiService';
import './index.css';

function App() {
  const [currentPage, setCurrentPage] = useState('alerts');
  const [currentUser, setCurrentUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  // ✅ Check if user already has a session
  useEffect(() => {
    const checkCurrentUser = async () => {
      try {
        const response = await getCurrentUser();
        setCurrentUser(response.data);
      } catch (error) {
        console.log("No active user session found.");
        setCurrentUser(null);
      } finally {
        setAuthLoading(false);
      }
    };
    checkCurrentUser();
  }, []);

  // ✅ Detect Upstox callback and route to LoginCallback page
  useEffect(() => {
    const url = new URL(window.location.href);
    const code = url.searchParams.get("code");
    const state = url.searchParams.get("state");

    if (code && window.location.pathname.includes("/login/callback")) {
      setCurrentPage("loginCallback");
    }
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
      setCurrentUser(null);
      setCurrentPage('alerts');
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  // ✅ Include LoginCallback as a page
  const renderPage = () => {
    switch (currentPage) {
      case 'alerts':
        return <AlertsPage setCurrentPage={setCurrentPage} />;
      case 'plans':
        return <TradePlansPage />;
      case 'journal':
        return <TradeJournalPage />;
      case 'loginCallback':
        return <LoginCallback setUser={setCurrentUser} setCurrentPage={setCurrentPage} />;
      default:
        return <AlertsPage setCurrentPage={setCurrentPage} />;
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex justify-center items-center">
        <p className="text-white">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white font-sans">
      <Navbar 
        currentPage={currentPage} 
        setCurrentPage={setCurrentPage}
        user={currentUser}
        onLogout={handleLogout}
      />
      
      <div className="container mx-auto">
        {renderPage()}
      </div>
    </div>
  );
}

export default App;
