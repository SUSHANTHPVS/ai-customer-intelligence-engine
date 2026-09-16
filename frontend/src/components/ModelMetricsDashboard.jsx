import React, { useEffect, useState } from 'react';
import useDashboardStore from '../store/dashboardStore';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import { FiActivity, FiTarget, FiTrendingUp } from 'react-icons/fi';
import JobsStatusPanel from './JobsStatusPanel';
import { apiClient } from '../api/client';

export const ModelMetricsDashboard = () => {
  const { models, fetchModelMetrics, loading } = useDashboardStore();
  const [retraining, setRetraining] = useState(false);

  useEffect(() => {
    fetchModelMetrics();
  }, []);

  const handleRetrain = async () => {
    try {
      setRetraining(true);
      await apiClient.models.retrainModel('churn_model');
      await fetchModelMetrics();
    } catch (error) {
      console.error('Retraining failed', error);
    } finally {
      setRetraining(false);
    }
  };

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

  const metricsList = (() => {
    const source = models.metrics || {};

    if (source.accuracy !== undefined || source.precision !== undefined || source.recall !== undefined) {
      return [{
        name: source.model_name || 'Active Dataset Model',
        accuracy: Number(source.accuracy) || 0,
        precision: Number(source.precision) || 0,
        recall: Number(source.recall) || 0,
        f1_score: Number(source.f1_score) || 0,
      }];
    }

    return Object.entries(source)
      .filter(([key, value]) => key !== 'timestamp' && value && typeof value === 'object' && !Array.isArray(value))
      .map(([name, value]) => ({
        name: name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
        accuracy: Number(value.accuracy) || 0,
        precision: Number(value.precision) || 0,
        recall: Number(value.recall) || 0,
        f1_score: Number(value.f1_score) || 0,
      }));
  })();

  const avgAccuracy = metricsList.length > 0 ? metricsList.reduce((sum, m) => sum + m.accuracy, 0) / metricsList.length : 0;
  const avgPrecision = metricsList.length > 0 ? metricsList.reduce((sum, m) => sum + m.precision, 0) / metricsList.length : 0;
  const avgRecall = metricsList.length > 0 ? metricsList.reduce((sum, m) => sum + m.recall, 0) / metricsList.length : 0;
  const driftDetected = !!models.metrics?.drift?.overall_drift;
  const retrainingScheduled = !!models.metrics?.retraining_scheduled;
  const featureImportanceData = Array.isArray(models.metrics?.feature_importances)
    ? models.metrics.feature_importances
        .slice(0, 8)
        .map((item) => ({
          feature: item.feature.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase()),
          importance: Number(item.importance) || 0,
        }))
        .sort((a, b) => b.importance - a.importance)
    : [];
  const scoreProfileData = [
    { metric: 'Accuracy', value: Math.min(Number(metricsList[0]?.accuracy || 0) * 100, 100) },
    { metric: 'Precision', value: Math.min(Number(metricsList[0]?.precision || 0) * 100, 100) },
    { metric: 'Recall', value: Math.min(Number(metricsList[0]?.recall || 0) * 100, 100) },
    { metric: 'F1', value: Math.min(Number(metricsList[0]?.f1_score || 0) * 100, 100) },
  ];

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

      <div className="bg-white rounded-lg shadow p-6 border-l-4 border-indigo-500">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-gray-600">Monitoring Status</p>
            <h3 className="text-xl font-bold text-gray-900 mt-1">Model Health & Automation</h3>
          </div>
          <button
            onClick={handleRetrain}
            disabled={retraining}
            className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-60"
          >
            {retraining ? 'Retraining...' : 'Run Retraining'}
          </button>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className={`rounded-lg border p-3 ${driftDetected ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'}`}>
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Drift Monitoring</p>
            <p className={`mt-2 text-lg font-bold ${driftDetected ? 'text-yellow-700' : 'text-green-700'}`}>
              {driftDetected ? 'Drift detected' : 'Stable'}
            </p>
          </div>
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Retraining Schedule</p>
            <p className="mt-2 text-lg font-bold text-blue-700">
              {retrainingScheduled ? 'Enabled' : 'Manual'}
            </p>
          </div>
          <div className="rounded-lg border border-purple-200 bg-purple-50 p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Leaderboard Rank</p>
            <p className="mt-2 text-lg font-bold text-purple-700">
              {models.leaderboard?.[0]?.dataset_id === models.metrics?.dataset_id ? 'Top model' : 'Tracked'}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Model Performance Over Time</h3>
          {models.performance?.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={models.performance}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="accuracy" stroke="#3B82F6" name="Accuracy" dot={true} />
                <Line type="monotone" dataKey="precision" stroke="#10B981" name="Precision" dot={true} />
                <Line type="monotone" dataKey="recall" stroke="#F59E0B" name="Recall" dot={true} />
                <Line type="monotone" dataKey="f1_score" stroke="#8B5CF6" name="F1" dot={true} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No performance data available</p>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Profile</h3>
          {scoreProfileData.some((item) => item.value > 0) ? (
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={scoreProfileData}>
                <PolarGrid stroke="#e5e7eb" />
                <PolarAngleAxis dataKey="metric" tick={{ fill: '#475569', fontSize: 12 }} />
                <PolarRadiusAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 10 }} />
                <Radar name="Score" dataKey="value" stroke="#8B5CF6" fill="#8B5CF6" fillOpacity={0.4} />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No score profile available</p>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Feature Importance</h3>
        {featureImportanceData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={featureImportanceData} layout="vertical" margin={{ left: 24 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 'dataMax + 0.1']} />
              <YAxis type="category" dataKey="feature" width={120} />
              <Tooltip />
              <Bar dataKey="importance" fill="#10B981" radius={[0, 8, 8, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-500 text-center py-8">No feature importance data available</p>
        )}
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Model Leaderboard</h3>

        {models.leaderboard?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-gray-200">
                <tr>
                  <th className="text-left py-2 px-4 font-semibold text-gray-900">Rank</th>
                  <th className="text-left py-2 px-4 font-semibold text-gray-900">Dataset</th>
                  <th className="text-left py-2 px-4 font-semibold text-gray-900">Model</th>
                  <th className="text-left py-2 px-4 font-semibold text-gray-900">Accuracy</th>
                  <th className="text-left py-2 px-4 font-semibold text-gray-900">Precision</th>
                  <th className="text-left py-2 px-4 font-semibold text-gray-900">Recall</th>
                  <th className="text-left py-2 px-4 font-semibold text-gray-900">F1</th>
                  <th className="text-left py-2 px-4 font-semibold text-gray-900">Drift</th>
                </tr>
              </thead>
              <tbody>
                {models.leaderboard.map((entry, idx) => (
                  <tr key={`${entry.dataset_id}-${entry.model_name}`} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm font-medium text-gray-900">#{idx + 1}</td>
                    <td className="py-3 px-4 text-sm text-gray-600">{entry.dataset_name}</td>
                    <td className="py-3 px-4 text-sm text-gray-600">{entry.model_name}</td>
                    <td className="py-3 px-4 text-sm text-gray-600">{Number(entry.accuracy || 0).toFixed(2)}</td>
                    <td className="py-3 px-4 text-sm text-gray-600">{Number(entry.precision || 0).toFixed(2)}</td>
                    <td className="py-3 px-4 text-sm text-gray-600">{Number(entry.recall || 0).toFixed(2)}</td>
                    <td className="py-3 px-4 text-sm text-gray-600">{Number(entry.f1_score || 0).toFixed(2)}</td>
                    <td className="py-3 px-4 text-sm">
                      <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${entry.drift_detected ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}`}>
                        {entry.drift_detected ? 'Alert' : 'Healthy'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">No leaderboard entries available yet</p>
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
