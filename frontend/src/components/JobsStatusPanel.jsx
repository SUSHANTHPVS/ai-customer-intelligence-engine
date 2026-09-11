import React, { useEffect, useState } from 'react';
import { FiServer, FiCheckCircle, FiXCircle, FiClock } from 'react-icons/fi';
import { apiClient } from '../api/client';

const JobsStatusPanel = () => {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await apiClient.jobs.getStatus();
        setStatus(data);
        setError(false);
      } catch (e) {
        setError(true);
      }
    };
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <FiServer /> Background Job Scheduler
      </h3>

      {error || !status ? (
        <p className="text-gray-500 text-center py-6">Job scheduler status unavailable</p>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm">
            {status.scheduler_running ? (
              <span className="flex items-center gap-1 text-green-700 bg-green-100 px-2 py-1 rounded-full font-semibold">
                <FiCheckCircle /> Running
              </span>
            ) : (
              <span className="flex items-center gap-1 text-red-700 bg-red-100 px-2 py-1 rounded-full font-semibold">
                <FiXCircle /> Stopped
              </span>
            )}
            {status.jobs?.[0]?.next_run_time && (
              <span className="text-gray-500 flex items-center gap-1">
                <FiClock /> Next run: {new Date(status.jobs[0].next_run_time).toLocaleTimeString()}
              </span>
            )}
          </div>

          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Recent Runs</h4>
            <div className="space-y-1">
              {(status.history || []).slice(0, 5).map((h, idx) => (
                <div key={idx} className="flex items-center justify-between text-xs bg-gray-50 rounded px-3 py-2">
                  <span className="font-medium text-gray-800">{h.job}</span>
                  <span className={h.status === 'success' ? 'text-green-600' : 'text-red-600'}>{h.status}</span>
                  <span className="text-gray-400">{new Date(h.ran_at).toLocaleTimeString()}</span>
                </div>
              ))}
              {(!status.history || status.history.length === 0) && (
                <p className="text-xs text-gray-400">No job runs recorded yet</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobsStatusPanel;
