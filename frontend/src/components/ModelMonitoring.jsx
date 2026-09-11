import React, { useState, useEffect } from 'react';
import { Activity, AlertTriangle, TrendingUp, BarChart3 } from 'react-icons/fa';

const ModelMonitoring = () => {
  const [modelMetrics, setModelMetrics] = useState([
    {
      name: 'Churn Prediction',
      accuracy: 0.872,
      precision: 0.89,
      recall: 0.85,
      f1: 0.87,
      predictions_24h: 2847,
      drift_detected: false,
      status: 'healthy'
    },
    {
      name: 'Revenue Forecast',
      accuracy: 0.925,
      precision: 0.93,
      recall: 0.92,
      f1: 0.925,
      predictions_24h: 2841,
      drift_detected: false,
      status: 'healthy'
    },
    {
      name: 'Engagement Score',
      accuracy: 0.894,
      precision: 0.91,
      recall: 0.88,
      f1: 0.895,
      predictions_24h: 2839,
      drift_detected: true,
      status: 'warning'
    },
    {
      name: 'Segmentation',
      accuracy: 0.945,
      precision: 0.95,
      recall: 0.94,
      f1: 0.945,
      predictions_24h: 2845,
      drift_detected: false,
      status: 'healthy'
    }
  ]);

  const getStatusBadge = (status, driftDetected) => {
    if (driftDetected) {
      return 'bg-yellow-900/30 text-yellow-400 border-yellow-500';
    }
    if (status === 'healthy') {
      return 'bg-green-900/30 text-green-400 border-green-500';
    }
    return 'bg-red-900/30 text-red-400 border-red-500';
  };

  const getStatusIcon = (status, driftDetected) => {
    if (driftDetected) {
      return <AlertTriangle className="text-yellow-400" size={16} />;
    }
    if (status === 'healthy') {
      return <Activity className="text-green-400" size={16} />;
    }
    return <AlertTriangle className="text-red-400" size={16} />;
  };

  return (
    <div className="space-y-4">
      {/* Overall Model Health */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <BarChart3 className="text-blue-400" /> Model Performance
        </h3>
        
        <div className="space-y-3">
          {modelMetrics.map((model, idx) => (
            <div
              key={idx}
              className={`rounded-lg border p-3 ${getStatusBadge(model.status, model.drift_detected)}`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  {getStatusIcon(model.status, model.drift_detected)}
                  <span className="font-semibold text-sm">{model.name}</span>
                </div>
                {model.drift_detected && (
                  <span className="text-xs bg-yellow-900/50 px-2 py-1 rounded">Drift Alert</span>
                )}
              </div>

              {/* Mini metrics */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-black/20 rounded p-2">
                  <p className="opacity-70">Accuracy</p>
                  <p className="font-bold">{(model.accuracy * 100).toFixed(1)}%</p>
                </div>
                <div className="bg-black/20 rounded p-2">
                  <p className="opacity-70">F1 Score</p>
                  <p className="font-bold">{(model.f1 * 100).toFixed(1)}%</p>
                </div>
                <div className="bg-black/20 rounded p-2">
                  <p className="opacity-70">Precision</p>
                  <p className="font-bold">{(model.precision * 100).toFixed(1)}%</p>
                </div>
                <div className="bg-black/20 rounded p-2">
                  <p className="opacity-70">Recall</p>
                  <p className="font-bold">{(model.recall * 100).toFixed(1)}%</p>
                </div>
              </div>

              <p className="text-xs mt-2 opacity-70">
                Predictions (24h): {model.predictions_24h.toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Data Drift Detection */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <TrendingUp className="text-cyan-400" /> Drift Detection
        </h3>

        <div className="space-y-2 text-sm">
          <div className="p-3 bg-green-900/20 border border-green-500 rounded-lg text-green-300">
            <p className="font-semibold mb-1">✓ Churn Model</p>
            <p className="text-xs opacity-80">Distribution stable • No significant drift detected</p>
          </div>

          <div className="p-3 bg-green-900/20 border border-green-500 rounded-lg text-green-300">
            <p className="font-semibold mb-1">✓ Revenue Model</p>
            <p className="text-xs opacity-80">Stable predictions • In control</p>
          </div>

          <div className="p-3 bg-yellow-900/20 border border-yellow-500 rounded-lg text-yellow-300">
            <p className="font-semibold mb-1">⚠ Engagement Model</p>
            <p className="text-xs opacity-80">Slight feature distribution shift • Monitor closely</p>
          </div>

          <div className="p-3 bg-green-900/20 border border-green-500 rounded-lg text-green-300">
            <p className="font-semibold mb-1">✓ Segmentation Model</p>
            <p className="text-xs opacity-80">Cluster centroids stable • No retraining needed</p>
          </div>
        </div>
      </div>

      {/* Retraining Recommendations */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
        <h3 className="text-lg font-bold text-white mb-3">Retraining Status</h3>

        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between p-2 bg-slate-700 rounded">
            <span>Last Churn Retrain</span>
            <span className="text-green-400">7 days ago</span>
          </div>
          <div className="flex items-center justify-between p-2 bg-slate-700 rounded">
            <span>Last Revenue Retrain</span>
            <span className="text-green-400">5 days ago</span>
          </div>
          <div className="flex items-center justify-between p-2 bg-slate-700 rounded">
            <span>Last Engagement Retrain</span>
            <span className="text-yellow-400">14 days ago</span>
          </div>
          <div className="flex items-center justify-between p-2 bg-slate-700 rounded">
            <span>Last Segment Retrain</span>
            <span className="text-green-400">3 days ago</span>
          </div>
        </div>

        <button className="mt-3 w-full py-2 px-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition">
          Schedule Manual Retraining
        </button>
      </div>
    </div>
  );
};

export default ModelMonitoring;
