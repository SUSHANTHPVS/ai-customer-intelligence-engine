import React, { useEffect, useRef, useState } from 'react';
import { getSocket } from '../lib/socket';
import { FiActivity, FiWifi, FiWifiOff } from 'react-icons/fi';

const riskColor = (level) => {
  if (level === 'HIGH') return 'border-red-400 bg-red-50 text-red-800';
  if (level === 'MEDIUM') return 'border-yellow-400 bg-yellow-50 text-yellow-800';
  return 'border-green-400 bg-green-50 text-green-800';
};

const LiveActivityFeed = () => {
  const [connected, setConnected] = useState(false);
  const [events, setEvents] = useState([]);
  const socketRef = useRef(null);

  useEffect(() => {
    const socket = getSocket();
    socketRef.current = socket;
    setConnected(socket.connected);

    const handleConnect = () => setConnected(true);
    const handleDisconnect = () => setConnected(false);
    const handleRiskAlert = (payload) => {
      setEvents((prev) => [payload, ...prev].slice(0, 25));
    };

    socket.on('connect', handleConnect);
    socket.on('disconnect', handleDisconnect);
    socket.on('risk_alert', handleRiskAlert);

    return () => {
      socket.off('connect', handleConnect);
      socket.off('disconnect', handleDisconnect);
      socket.off('risk_alert', handleRiskAlert);
    };
  }, []);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <FiActivity /> Live Risk Monitoring Feed
        </h3>
        <span className={`flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full ${
          connected ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
        }`}>
          {connected ? <FiWifi /> : <FiWifiOff />} {connected ? 'Live' : 'Connecting...'}
        </span>
      </div>

      <p className="text-sm text-gray-500 mb-4">
        Streamed in real time over WebSockets — new churn-risk signals appear here as they are detected.
      </p>

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {events.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">Waiting for the first event...</p>
        ) : (
          events.map((event, idx) => (
            <div
              key={`${event.customer_id}-${event.timestamp}-${idx}`}
              className={`flex items-center justify-between border-l-4 rounded px-3 py-2 text-sm ${riskColor(event.risk_level)}`}
            >
              <div>
                <span className="font-semibold">{event.customer_id}</span>
                <span className="ml-2">churn risk score {Number(event.churn_risk_score ?? 0).toFixed(2)}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-semibold">{event.risk_level}</span>
                <span className="text-xs opacity-70">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default LiveActivityFeed;
