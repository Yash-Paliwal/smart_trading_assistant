// src/App.js

import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import AlertsPage from './pages/AlertsPage';
import TradePlansPage from './pages/TradePlansPage';
import TradeJournalPage from './pages/TradeJournalPage';
import VirtualTradingPage from './pages/VirtualTradingPage';
import LiveTradingDashboard from './components/LiveTradingDashboard';

import LoginCallback from './pages/LoginCallback';
import { getCurrentUser, logout } from './api/apiService';
import './App.css';
import './index.css';
import { ToastProvider } from './components/ToastProvider';

function App() {
  const [currentPage, setCurrentPage] = useState('alerts');
  const [currentUser, setCurrentUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  // Check if user already has a session
  useEffect(() => {
    const checkCurrentUser = async () => {
      try {
        const response = await getCurrentUser();
        if (response.data && response.data.username) {
          setCurrentUser(response.data);
          console.log("User session found:", response.data.username);
        } else {
          setCurrentUser(null);
          console.log("No valid user session found.");
        }
      } catch (error) {
        console.log("No active user session found:", error.message);
        setCurrentUser(null);
      } finally {
        setAuthLoading(false);
      }
    };
    checkCurrentUser();
  }, []);

  // Detect Upstox callback and route to LoginCallback page
  useEffect(() => {
    const url = new URL(window.location.href);
    const code = url.searchParams.get("code");
    // eslint-disable-next-line no-unused-vars
    const state = url.searchParams.get("state");

    if (code) {
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

  // Include LoginCallback as a page
  const renderPage = () => {
    switch (currentPage) {
      case 'alerts':
        return <AlertsPage setCurrentPage={setCurrentPage} />;
      case 'plans':
        return <TradePlansPage />;
      case 'journal':
        return <TradeJournalPage />;
      case 'virtual-trading':
        return <VirtualTradingPage />;
      case 'live-dashboard':
        return <LiveTradingDashboard userId={currentUser?.username} />;
      
      
      case 'loginCallback':
        return <LoginCallback setUser={setCurrentUser} setCurrentPage={setCurrentPage} />;
      default:
        return <AlertsPage setCurrentPage={setCurrentPage} />;
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <ToastProvider>
      <div className="App">
        <Navbar 
          currentPage={currentPage} 
          setCurrentPage={setCurrentPage}
          user={currentUser}
          onLogout={handleLogout}
        />
        <main>
          {renderPage()}
        </main>
      </div>
    </ToastProvider>
  );
}

export default App;
