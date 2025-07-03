// src/pages/LoginCallback.jsx

import { useEffect } from 'react';

const LoginCallback = ({ setUser, setCurrentPage }) => {
  useEffect(() => {
    const url = new URL(window.location.href);
    const code = url.searchParams.get("code");
    const state = url.searchParams.get("state");

    if (code) {
      fetch(`/api/auth/upstox/callback/?code=${code}&state=${state}`, {
        method: "GET",
        credentials: "include",
      })
        .then(res => res.json())
        .then(data => {
          if (data.message === "Login successful") {
            return fetch("/api/auth/user/", {
              method: "GET",
              credentials: "include",
            });
          }
          throw new Error("Login failed");
        })
        .then(res => res.json())
        .then(user => {
          setUser(user);
          setCurrentPage("alerts");
          window.history.replaceState({}, "", "/"); // clean up URL
        })
        .catch(err => {
          console.error("Login callback failed:", err);
        });
    }
  }, [setUser, setCurrentPage]);

  return <p className="text-center p-10">Logging you in...</p>;
};

export default LoginCallback;
