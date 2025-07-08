// src/setupProxy.js

const { createProxyMiddleware } = require('http-proxy-middleware');

// --- DEBUGGING STEP ---
// This message will appear in the terminal where you run "npm start"
// if this file is being loaded correctly by React.
console.log("✅ setupProxy.js is being loaded!");
// --- END DEBUGGING STEP ---

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://127.0.0.1:8000',
      changeOrigin: true
    })
  );
};
