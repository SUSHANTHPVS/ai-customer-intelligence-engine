import React, { useState, useEffect } from 'react';
import { PieChart, Pie, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

const DashboardCharts = ({
  riskDistribution = [],
  segmentDistribution = [],
  engagementTrend = []
}) => {
  const hasData = riskDistribution.length > 0 || segmentDistribution.length > 0 || engagementTrend.length > 0;
  const SEGMENT_COLORS = {
    Standard: '#3b82f6',
    VIP: '#a855f7',
    'At-Risk': '#ef4444',
    Dormant: '#6b7280',
  };

  if (!hasData) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 text-gray-500 text-center">
        Live chart data is not available yet. The API is still preparing customer metrics.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
        <h3 className="text-lg font-bold text-white mb-4">Churn Risk Distribution</h3>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={riskDistribution}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              dataKey="value"
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            >
              {riskDistribution.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color || '#3b82f6'} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => `${value.toLocaleString()}`} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
        <h3 className="text-lg font-bold text-white mb-4">Customer Segments</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={segmentDistribution}>
            <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
            <XAxis dataKey="name" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
              formatter={(value) => value.toLocaleString()}
            />
            <Bar dataKey="value" radius={[8, 8, 0, 0]}>
              {segmentDistribution.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={SEGMENT_COLORS[entry.name] || '#3b82f6'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
        <h3 className="text-lg font-bold text-white mb-4">Engagement Trend</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={engagementTrend}>
            <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
            <XAxis dataKey="time" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
            />
            <Bar dataKey="avg_engagement" fill="#06b6d4" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default DashboardCharts;
