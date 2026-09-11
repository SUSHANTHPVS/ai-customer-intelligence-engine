import React, { useEffect, useState } from 'react';
import { FiBell } from 'react-icons/fi';
import useNotificationStore from '../store/notificationStore';

const NotificationBell = () => {
  const { notifications, unreadCount, init, markAllRead } = useNotificationStore();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    init();
  }, [init]);

  const handleToggle = () => {
    setOpen((o) => !o);
    if (!open) markAllRead();
  };

  return (
    <div className="relative">
      <button
        onClick={handleToggle}
        className="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
      >
        <FiBell size={20} />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-96 overflow-y-auto">
          <div className="px-4 py-3 border-b border-gray-100 font-semibold text-gray-900 text-sm">
            High Churn Risk Alerts
          </div>
          {notifications.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-6">No alerts yet</p>
          ) : (
            notifications.map((n) => (
              <div key={n.id} className="px-4 py-3 border-b border-gray-50 hover:bg-gray-50 text-sm">
                <div className="flex justify-between">
                  <span className="font-medium text-gray-900">{n.customer_id}</span>
                  <span className="text-red-600 font-semibold">HIGH</span>
                </div>
                <p className="text-gray-500 text-xs mt-1">
                  Risk score {Number(n.churn_risk_score ?? 0).toFixed(2)} • {new Date(n.timestamp).toLocaleTimeString()}
                </p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
