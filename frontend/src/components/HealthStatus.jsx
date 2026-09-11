import React, { useEffect } from 'react';
import useDashboardStore from '../store/dashboardStore';
import { FiRefreshCw, FiAlertCircle, FiCheckCircle } from 'react-icons/fi';

export const HealthStatus = () => {
  const { apiHealth, checkHealth, loading } = useDashboardStore();

  useEffect(() => {
    checkHealth();
  }, []);

  if (!apiHealth) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center gap-3">
          <FiAlertCircle className="text-red-500 text-xl" />
          <div>
            <p className="font-semibold text-red-800">API Connection Failed</p>
            <p className="text-sm text-red-600">Unable to reach backend service</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
      <div className="flex items-center gap-3">
        <FiCheckCircle className="text-green-500 text-xl" />
        <div>
          <p className="font-semibold text-green-800">API Healthy</p>
          <p className="text-sm text-green-600">
            {apiHealth.status} • {apiHealth.timestamp}
          </p>
        </div>
      </div>
    </div>
  );
};

export const RefreshButton = () => {
  const { loading, refreshAll } = useDashboardStore();

  return (
    <button
      onClick={refreshAll}
      disabled={loading}
      className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
    >
      <FiRefreshCw className={loading ? 'animate-spin' : ''} />
      {loading ? 'Refreshing...' : 'Refresh'}
    </button>
  );
};

export default HealthStatus;
