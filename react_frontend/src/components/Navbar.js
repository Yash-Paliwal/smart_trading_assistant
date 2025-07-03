// src/components/Navbar.js

import React from 'react';

const Navbar = ({ currentPage, setCurrentPage, user, onLogout }) => {
  // A helper function to apply the correct CSS classes for the active link
  const getNavLinkClasses = (pageName) => 
    `px-3 py-2 rounded-md text-sm font-medium cursor-pointer transition-colors ${
      currentPage === pageName 
      ? 'bg-blue-600 text-white' 
      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
    }`;

  return (
    <nav className="bg-gray-800 shadow-lg sticky top-0 z-40">
      <div className="container mx-auto px-4 md:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <span className="text-white font-bold text-xl">Smart Trader</span>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <a onClick={() => setCurrentPage('alerts')} className={getNavLinkClasses('alerts')}>
                  Radar Alerts
                </a>
                <a onClick={() => setCurrentPage('plans')} className={getNavLinkClasses('plans')}>
                  Trade Plans
                </a>
                <a onClick={() => setCurrentPage('journal')} className={getNavLinkClasses('journal')}>
                  Trade Journal
                </a>
              </div>
            </div>
          </div>
          <div className="flex items-center">
            {/* --- DYNAMIC LOGIN/LOGOUT UI --- */}
            {user ? (
              // If a user is logged in, show their name and a Logout button
              <div className="flex items-center space-x-4">
                <span className="text-gray-300 text-sm">Welcome, {user.first_name || user.username}</span>
                <button 
                  onClick={onLogout}
                  className="bg-red-600 text-white hover:bg-red-700 px-4 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Logout
                </button>
              </div>
            ) : (
              // If no user is logged in, show the Login button
              <a 
                href="/api/auth/upstox/login/" 
                className="bg-green-600 text-white hover:bg-green-700 px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Login with Upstox
              </a>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
