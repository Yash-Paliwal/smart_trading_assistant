// src/pages/LoginCallback.jsx

import { useEffect, useState } from 'react';

const LoginCallback = ({ setUser, setCurrentPage }) => {
  const [status, setStatus] = useState('Logging you in...');
  const [error, setError] = useState(null);

  // Helper to check if user is already authenticated
  const checkUserSession = async () => {
    try {
      setStatus('Checking session...');
      const res = await fetch('/api/auth/user/', {
        method: 'GET',
        credentials: 'include',
      });
      if (res.ok) {
        const user = await res.json();
        setUser(user);
        setStatus('Login successful! Redirecting...');
        setCurrentPage('alerts');
        window.history.replaceState({}, '', '/');
        return true;
      }
    } catch (e) {
      // ignore
    }
    return false;
  };

  useEffect(() => {
    const url = new URL(window.location.href);
    const code = url.searchParams.get('code');
    const state = url.searchParams.get('state');

    if (code) {
      setStatus('Authenticating with Upstox...');
      fetch(`/api/auth/upstox/callback/?code=${code}&state=${state}`, {
        method: 'GET',
        credentials: 'include',
      })
        .then(res => {
          if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
          }
          return res.json();
        })
        .then(data => {
          if (data.message === 'Login successful') {
            setStatus('Loading user profile...');
            return fetch('/api/auth/user/', {
              method: 'GET',
              credentials: 'include',
            });
          }
          throw new Error(data.message || 'Login failed');
        })
        .then(res => {
          if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
          }
          return res.json();
        })
        .then(user => {
          setStatus('Login successful! Redirecting...');
          setUser(user);
          setCurrentPage('alerts');
          window.history.replaceState({}, '', '/');
        })
        .catch(async err => {
          // On error, check if user is already authenticated
          const alreadyLoggedIn = await checkUserSession();
          if (!alreadyLoggedIn) {
            setError(err.message || 'Login failed. Please try again.');
            setStatus('Login failed');
          }
        });
    } else {
      setError('No authorization code found. Please try logging in again.');
      setStatus('Login failed');
    }
    // eslint-disable-next-line
  }, [setUser, setCurrentPage]);

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center p-8 bg-white rounded-lg shadow-lg max-w-md">
          <div className="text-red-500 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">Login Failed</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.href = '/api/auth/upstox/login/'}
            className="bg-gradient-to-r from-green-500 to-emerald-500 text-white px-6 py-2 rounded-lg hover:from-green-600 hover:to-emerald-600 transition-all duration-200"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center p-8 bg-white rounded-lg shadow-lg max-w-md">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <h2 className="text-xl font-bold text-gray-800 mb-2">Logging In</h2>
        <p className="text-gray-600">{status}</p>
      </div>
    </div>
  );
};

export default LoginCallback;
