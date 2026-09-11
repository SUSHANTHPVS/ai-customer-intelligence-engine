import React, { useEffect, useState } from 'react';
import { FiGrid } from 'react-icons/fi';
import { apiClient } from '../api/client';

const cellColor = (pct) => {
  if (pct === null || pct === undefined) return 'bg-gray-50 text-gray-300';
  if (pct >= 70) return 'bg-green-600 text-white';
  if (pct >= 50) return 'bg-green-400 text-white';
  if (pct >= 30) return 'bg-yellow-400 text-gray-900';
  if (pct >= 15) return 'bg-orange-400 text-white';
  return 'bg-red-400 text-white';
};

const CohortAnalysis = () => {
  const [cohorts, setCohorts] = useState([]);
  const [maxOffset, setMaxOffset] = useState(6);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiClient.analytics.getCohortRetention()
      .then(({ data }) => {
        setCohorts(data.cohorts || []);
        setMaxOffset(data.max_month_offset ?? 6);
      })
      .catch(() => setError('Failed to load cohort retention data'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading cohort retention...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center gap-2">
          <FiGrid /> Cohort Retention Analysis
        </h3>
        <p className="text-sm text-gray-500 mb-4">
          Customers grouped by signup month, tracking the percentage still active in each subsequent month — computed live from event activity.
        </p>

        {error && <p className="text-sm text-red-500">{error}</p>}

        {!error && cohorts.length === 0 && (
          <p className="text-sm text-gray-400">Not enough signup/event history to compute cohorts yet.</p>
        )}

        {!error && cohorts.length > 0 && (
          <div className="overflow-x-auto">
            <table className="text-sm border-collapse">
              <thead>
                <tr>
                  <th className="text-left py-2 px-3 font-semibold text-gray-900">Cohort</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-900">Size</th>
                  {Array.from({ length: maxOffset + 1 }, (_, i) => (
                    <th key={i} className="text-center py-2 px-3 font-semibold text-gray-900">Month {i}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {cohorts.map((c) => (
                  <tr key={c.cohort_month} className="border-t border-gray-100">
                    <td className="py-2 px-3 font-medium text-gray-700">{c.cohort_month}</td>
                    <td className="py-2 px-3 text-gray-500">{c.cohort_size.toLocaleString()}</td>
                    {c.retention.map((pct, idx) => (
                      <td key={idx} className="py-1 px-1 text-center">
                        <div className={`rounded px-2 py-1.5 text-xs font-semibold ${cellColor(pct)}`}>
                          {pct === null || pct === undefined ? '—' : `${pct}%`}
                        </div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default CohortAnalysis;
