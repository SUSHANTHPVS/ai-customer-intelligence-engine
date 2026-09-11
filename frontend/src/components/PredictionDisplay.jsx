import React from 'react';
import { AlertTriangle, TrendingUp, Users, Activity } from 'react-icons/fa';

const PredictionDisplay = ({ predictions }) => {
  const { customer_id, churn, revenue, engagement, segment, timestamp } = predictions;

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'CRITICAL':
        return 'text-red-500 bg-red-900/20 border-red-500';
      case 'HIGH':
        return 'text-orange-500 bg-orange-900/20 border-orange-500';
      case 'MEDIUM':
        return 'text-yellow-500 bg-yellow-900/20 border-yellow-500';
      case 'LOW':
        return 'text-green-500 bg-green-900/20 border-green-500';
      default:
        return 'text-gray-500';
    }
  };

  const getEngagementColor = (level) => {
    switch (level) {
      case 'HIGH':
        return 'text-green-400 bg-green-900/20 border-green-500';
      case 'MEDIUM':
        return 'text-yellow-400 bg-yellow-900/20 border-yellow-500';
      case 'LOW':
        return 'text-red-400 bg-red-900/20 border-red-500';
      default:
        return 'text-gray-400';
    }
  };

  const getSegmentColor = (segment) => {
    switch (segment) {
      case 'VIP':
        return 'bg-purple-900/20 border-purple-500 text-purple-400';
      case 'AT_RISK':
        return 'bg-red-900/20 border-red-500 text-red-400';
      case 'DORMANT':
        return 'bg-gray-900/20 border-gray-500 text-gray-400';
      case 'STANDARD':
        return 'bg-blue-900/20 border-blue-500 text-blue-400';
      default:
        return 'bg-slate-700 border-slate-600 text-slate-300';
    }
  };

  return (
    <div className="space-y-4">
      {/* Customer Info Header */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-slate-400 text-sm">Customer ID</p>
            <p className="text-2xl font-bold text-white">{customer_id}</p>
          </div>
          <div className="text-right">
            <p className="text-slate-400 text-sm">Prediction Time</p>
            <p className="text-sm text-slate-300">
              {new Date(timestamp).toLocaleTimeString()}
            </p>
          </div>
        </div>
      </div>

      {/* Predictions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Churn Risk */}
        <div className={`rounded-xl border p-6 ${getRiskColor(churn.risk_level)}`}>
          <div className="flex items-start justify-between mb-3">
            <div>
              <p className="text-sm opacity-70 mb-1">Churn Risk</p>
              <p className="text-3xl font-bold">{(churn.churn_probability * 100).toFixed(1)}%</p>
            </div>
            <AlertTriangle size={28} />
          </div>
          <div className="flex items-center gap-2 mt-4">
            <div className="h-2 flex-1 bg-black/20 rounded-full overflow-hidden">
              <div
                className="h-full bg-current transition-all"
                style={{ width: `${churn.churn_probability * 100}%` }}
              />
            </div>
            <span className="text-sm font-semibold">{churn.risk_level}</span>
          </div>
        </div>

        {/* Revenue Forecast */}
        <div className="rounded-xl border bg-emerald-900/20 border-emerald-500 text-emerald-400 p-6">
          <div className="flex items-start justify-between mb-3">
            <div>
              <p className="text-sm opacity-70 mb-1">Revenue Forecast</p>
              <p className="text-3xl font-bold">${revenue.revenue_forecast.toFixed(2)}</p>
            </div>
            <TrendingUp size={28} />
          </div>
          <div className="mt-4">
            <p className="text-sm">
              Bracket: <span className="font-semibold">{revenue.revenue_bracket}</span>
            </p>
          </div>
        </div>

        {/* Engagement Score */}
        <div className={`rounded-xl border p-6 ${getEngagementColor(engagement.engagement_level)}`}>
          <div className="flex items-start justify-between mb-3">
            <div>
              <p className="text-sm opacity-70 mb-1">Engagement Score</p>
              <p className="text-3xl font-bold">{engagement.engagement_score.toFixed(1)}</p>
            </div>
            <Activity size={28} />
          </div>
          <div className="flex items-center gap-2 mt-4">
            <div className="h-2 flex-1 bg-black/20 rounded-full overflow-hidden">
              <div
                className="h-full bg-current transition-all"
                style={{ width: `${(engagement.engagement_score / 100) * 100}%` }}
              />
            </div>
            <span className="text-sm font-semibold">{engagement.engagement_level}</span>
          </div>
        </div>

        {/* Customer Segment */}
        <div className={`rounded-xl border p-6 ${getSegmentColor(segment.segment_name)}`}>
          <div className="flex items-start justify-between mb-3">
            <div>
              <p className="text-sm opacity-70 mb-1">Customer Segment</p>
              <p className="text-3xl font-bold">{segment.segment_name}</p>
            </div>
            <Users size={28} />
          </div>
          <p className="text-sm mt-3 opacity-90">{segment.description}</p>
        </div>
      </div>

      {/* Recommendations */}
      <div className="bg-blue-900/20 border border-blue-500 rounded-xl p-4">
        <h3 className="text-blue-400 font-semibold mb-3">Recommendations</h3>
        <ul className="space-y-2 text-sm text-blue-200">
          {churn.risk_level === 'CRITICAL' && (
            <li>🚨 High churn risk - Prioritize retention campaigns immediately</li>
          )}
          {churn.risk_level === 'HIGH' && (
            <li>⚠️ Elevated churn risk - Consider personalized offers</li>
          )}
          {engagement.engagement_level === 'LOW' && (
            <li>📧 Low engagement - Send re-engagement emails or promotions</li>
          )}
          {revenue.revenue_bracket === 'HIGH' && (
            <li>💰 High-value customer - Invest in premium support</li>
          )}
          {segment.segment_name === 'VIP' && (
            <li>⭐ VIP customer - Dedicate account manager for personalized service</li>
          )}
          {segment.segment_name === 'AT_RISK' && (
            <li>🔴 At-risk segment - Focus on value proposition and engagement</li>
          )}
        </ul>
      </div>
    </div>
  );
};

export default PredictionDisplay;
