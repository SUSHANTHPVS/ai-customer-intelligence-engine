import React, { useEffect } from 'react';
import useDashboardStore from '../store/dashboardStore';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { FiActivity, FiTarget, FiTrendingUp } from 'react-icons/fi';
import JobsStatusPanel from './JobsStatusPanel';

export const ModelMetricsDashboard = () => {
  const { models, fetchModelMetrics, loading } = useDashboardStore();

  useEffect(() => {
    fetchModelMetrics();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading model metrics...</p>
        </div>
      </div>
    );
  }

  const metricsList = Object.entries(models.metrics || {})
    .filter(([key, value]) => key !== 'timestamp' && value && typeof value === 'object')
    .map(([name, value]) => ({
      name: name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
      accuracy: Number(value.accuracy) || 0,
      precision: Number(value.precision) || 0,
      recall: Number(value.recall) || 0,
      f1_score: Number(value.f1_score) || 0,
    }));

  const avgAccuracy = metricsList.length > 0 ? metricsList.reduce((sum, m) => sum + m.accuracy, 0) / metricsList.length : 0;
  const avgPrecision = metricsList.length > 0 ? metricsList.reduce((sum, m) => sum + m.precision, 0) / metricsList.length : 0;
  const avgRecall = metricsList.length > 0 ? metricsList.reduce((sum, m) => sum + m.recall, 0) / metricsList.length : 0;

  return (
    <div className="space-y-6">
      {/* Model Performance KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Model Accuracy</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {(avgAccuracy * 100).toFixed(1)}%
              </p>
            </div>
            <FiTarget className="text-blue-500 text-3xl opacity-20" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Precision Score</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {avgPrecision.toFixed(2)}
              </p>
            </div>
            <FiTrendingUp className="text-green-500 text-3xl opacity-20" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-purple-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Recall Score</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {avgRecall.toFixed(2)}
              </p>
            </div>
            <FiActivity className="text-purple-500 text-3xl opacity-20" />
          </div>
        </div>
      </div>

      {/* Model Performance Over Time */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Model Performance Over Time</h3>
        {models.performance?.length > 0 ? (
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={models.performance}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="accuracy"
                stroke="#3B82F6"
                name="Accuracy"
                dot={true}
              />
              <Line
                type="monotone"
                dataKey="precision"
                stroke="#10B981"
                name="Precision"
                dot={true}
              />
              <Line
                type="monotone"
                dataKey="recall"
                stroke="#F59E0B"
                name="Recall"
                dot={true}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-500 text-center py-8">No performance data available</p>
        )}
      </div>

      {/* Detailed Metrics Table */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Detailed Metrics</h3>
        {metricsList.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-gray-200">
                <tr>
                  <th className="text-left py-2 px-4 font-semibold text-gray-900">Model</th>
                  <th className="text-left py-2 px-4 font-semibold text-gray-900">Accuracy</th>
                  <th className="text-left py-2 px-4 font-semibold text-gray-900">Precision</th>
                  <th className="text-left py-2 px-4 font-semibold text-gray-900">Recall</th>
                  <th className="text-left py-2 px-4 font-semibold text-gray-900">F1 Score</th>
                </tr>
              </thead>
              <tbody>
                {metricsList.map((metric, idx) => (
                  <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm font-medium text-gray-900">{metric.name}</td>
                    <td className="py-3 px-4 text-sm text-gray-600">{metric.accuracy.toFixed(2)}</td>
                    <td className="py-3 px-4 text-sm text-gray-600">{metric.precision.toFixed(2)}</td>
                    <td className="py-3 px-4 text-sm text-gray-600">{metric.recall.toFixed(2)}</td>
                    <td className="py-3 px-4 text-sm text-gray-600">{metric.f1_score.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">No detailed metrics available</p>
        )}
      </div>

      <JobsStatusPanel />
    </div>
  );
};

export default ModelMetricsDashboard;
