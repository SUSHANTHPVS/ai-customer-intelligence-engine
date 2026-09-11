import React, { useState, useEffect } from 'react';
import { PieChart, Pie, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

const DashboardCharts = () => {
  const [riskDistribution, setRiskDistribution] = useState([
    { name: 'Low Risk', value: 4500, color: '#22c55e' },
    { name: 'Medium Risk', value: 2800, color: '#eab308' },
    { name: 'High Risk', value: 1800, color: '#f97316' },
    { name: 'Critical Risk', value: 900, color: '#ef4444' }
  ]);

  const [segmentDistribution, setSegmentDistribution] = useState([
    { name: 'Standard', value: 3200 },
    { name: 'VIP', value: 1500 },
    { name: 'At-Risk', value: 3100 },
    { name: 'Dormant', value: 2200 }
  ]);

  const [engagementTrend, setEngagementTrend] = useState([
    { time: '00:00', avg_engagement: 45 },
    { time: '06:00', avg_engagement: 52 },
    { time: '12:00', avg_engagement: 68 },
    { time: '18:00', avg_engagement: 75 },
    { time: '23:59', avg_engagement: 62 }
  ]);

  const SEGMENT_COLORS = {
    'Standard': '#3b82f6',
    'VIP': '#a855f7',
    'At-Risk': '#ef4444',
    'Dormant': '#6b7280'
  };

  return (
    <div className="space-y-6">
      {/* Churn Risk Distribution */}
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
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => `${value.toLocaleString()}`} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Segment Distribution */}
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
                <Cell key={`cell-${index}`} fill={SEGMENT_COLORS[entry.name]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Engagement Trend */}
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

      {/* Key Metrics */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
        <h3 className="text-lg font-bold text-white mb-4">Quick Stats</h3>
        <div className="space-y-3">
          <div className="flex justify-between items-center p-3 bg-slate-700 rounded-lg">
            <span className="text-slate-300">Total Customers</span>
            <span className="text-white font-bold">10,000</span>
          </div>
          <div className="flex justify-between items-center p-3 bg-slate-700 rounded-lg">
            <span className="text-slate-300">Avg Churn Risk</span>
            <span className="text-yellow-400 font-bold">23.5%</span>
          </div>
          <div className="flex justify-between items-center p-3 bg-slate-700 rounded-lg">
            <span className="text-slate-300">Avg Engagement</span>
            <span className="text-green-400 font-bold">65.2</span>
          </div>
          <div className="flex justify-between items-center p-3 bg-slate-700 rounded-lg">
            <span className="text-slate-300">Avg Revenue</span>
            <span className="text-cyan-400 font-bold">$425.80</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardCharts;
