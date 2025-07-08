import React, { useEffect } from 'react';

const toastColors = {
  success: 'from-green-500 to-emerald-500',
  error: 'from-red-500 to-pink-500',
  info: 'from-blue-500 to-cyan-500',
  warning: 'from-yellow-500 to-orange-500',
};

const Toast = ({ message, type = 'info', onClose, duration = 4000 }) => {
  useEffect(() => {
    if (!duration) return;
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [onClose, duration]);

  return (
    <div
      className={`fixed top-6 right-6 z-50 px-6 py-4 rounded-xl shadow-lg text-white font-semibold bg-gradient-to-r ${toastColors[type] || toastColors.info} flex items-center gap-3 animate-fade-in`}
      role="alert"
      style={{ minWidth: 240 }}
    >
      <span>{message}</span>
      <button
        onClick={onClose}
        className="ml-4 text-white hover:text-gray-200 text-xl font-bold focus:outline-none"
        aria-label="Close notification"
      >
        &times;
      </button>
    </div>
  );
};

export default Toast; 