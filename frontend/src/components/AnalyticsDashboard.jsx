import React, { useEffect } from 'react';
import useDashboardStore from '../store/dashboardStore';
import {
  PieChart,
  Pie,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  AreaChart,
  Area,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import { FiTrendingUp, FiUsers, FiAlertTriangle, FiDownload, FiZap } from 'react-icons/fi';
import { apiClient } from '../api/client';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

const downloadBlob = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  window.URL.revokeObjectURL(url);
};

export const AnalyticsDashboard = () => {
  const { analytics, fetchAnalytics, insight, fetchInsight, loading } = useDashboardStore();

  useEffect(() => {
    fetchAnalytics();
    fetchInsight();
  }, []);

  const engagementStats = analytics.engagement || {};
  const engagementMetricsData = Object.keys(engagementStats).length > 0 ? [
    { metric: 'Avg Engagement', value: Number(engagementStats.avg_engagement) || 0 },
    { metric: 'Avg Active Days', value: Number(engagementStats.avg_active_days) || 0 },
    { metric: 'Avg Feature Usage', value: Number(engagementStats.avg_feature_usage) || 0 },
  ] : [];

  const ltvStats = analytics.ltv || {};
  const ltvChartData = ltvStats.actual_ltv !== undefined ? [
    { name: 'Lifetime Value', 'Actual LTV': Number(ltvStats.actual_ltv) || 0, 'Predicted LTV': Number(ltvStats.predicted_ltv) || 0 },
  ] : [];

  const highRiskCount = analytics.churn?.find((c) => c.risk_level === 'HIGH')?.count || 0;
  const totalCustomers = Number(engagementStats.total_customers) || 0;
  const hasLiveAnalytics = totalCustomers > 0 || (analytics.segmentation?.length ?? 0) > 0 || (analytics.churn?.length ?? 0) > 0;
  const customerHealthScore = Math.max(0, Math.min(100, Number(engagementStats.avg_engagement) || 0));
  const riskDistributionData = analytics.churn?.length > 0
    ? analytics.churn.map((item) => ({
        name: item.risk_level,
        count: Number(item.count) || 0,
        percentage: Number(item.percentage) || 0,
      }))
    : [];
  const engagementProfileData = [
    { metric: 'Engagement', value: Math.min(Number(engagementStats.avg_engagement) || 0, 100) },
    { metric: 'Active Days', value: Math.min(Number(engagementStats.avg_active_days) || 0, 100) },
    { metric: 'Feature Use', value: Math.min(Number(engagementStats.avg_feature_usage) || 0, 100) },
    { metric: 'Retention', value: Math.max(0, 100 - (highRiskCount || 0) * 0.75) },
    { metric: 'Health', value: Math.max(0, 100 - (analytics.churn?.find((c) => c.risk_level === 'HIGH')?.percentage || 0) * 1.4) },
  ];
  const aiActions = [
    {
      title: 'Retention Priority',
      description: highRiskCount > 0
        ? `${highRiskCount} customers are currently in the high-risk band and should get immediate outreach.`
        : 'No high-risk customers detected right now. Keep monitoring for emerging churn patterns.',
      tone: 'border-red-200 bg-red-50 text-red-800',
    },
    {
      title: 'Engagement Opportunity',
      description: Number(engagementStats.avg_engagement || 0) < 60
        ? `Average engagement is ${(Number(engagementStats.avg_engagement) || 0).toFixed(1)}%. Focus onboarding nudges on low-activity segments.`
        : `Average engagement is ${(Number(engagementStats.avg_engagement) || 0).toFixed(1)}%, which is healthy. Use this window to push upsell campaigns.`,
      tone: 'border-yellow-200 bg-yellow-50 text-yellow-800',
    },
    {
      title: 'Revenue Upside',
      description: Number(ltvStats.predicted_ltv || 0) > 0
        ? `Predicted LTV is $${Number(ltvStats.predicted_ltv || 0).toLocaleString()} — ideal for VIP and expansion offers.`
        : 'Predicted LTV is not available yet. Train the churn model to unlock revenue forecasting.',
      tone: 'border-green-200 bg-green-50 text-green-800',
    },
  ];

  const handleExportReport = async () => {
    const response = await apiClient.export.analyticsReport();
    downloadBlob(response.data, 'analytics_report.csv');
  };

  const handleExportReportPdf = async () => {
    const response = await apiClient.export.analyticsReportPdf();
    downloadBlob(response.data, 'analytics_report.pdf');
  };

  const handleExportCustomers = async () => {
    const response = await apiClient.export.customers({});
    downloadBlob(response.data, 'customers_export.csv');
  };

  const handleExportCustomersXlsx = async () => {
    const response = await apiClient.export.customersXlsx({});
    downloadBlob(response.data, 'customers_export.xlsx');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Automated Insights */}
      {insight && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <FiZap className="text-yellow-500" /> Automated Insight
          </h3>
          <div
            className={`text-sm px-4 py-2 rounded-lg border-l-4 ${
              insight.type === 'warning' ? 'border-red-400 bg-red-50 text-red-800' :
              insight.type === 'positive' ? 'border-green-400 bg-green-50 text-green-800' :
              insight.type === 'opportunity' ? 'border-purple-400 bg-purple-50 text-purple-800' :
              'border-blue-400 bg-blue-50 text-blue-800'
            }`}
          >
            {insight.text}
          </div>
        </div>
      )}

      <div className="hero-panel rounded-2xl p-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/15 via-indigo-500/15 to-emerald-400/10" />
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-blue-700">Executive overview</p>
            <h3 className="mt-2 text-2xl font-bold text-slate-900">
              {hasLiveAnalytics ? (
                <>Average customer engagement is <span className="text-blue-700">{customerHealthScore.toFixed(1)}%</span></>
              ) : (
                <span className="text-slate-500">Waiting for live customer data</span>
              )}
            </h3>
            <p className="mt-2 max-w-xl text-sm text-slate-600">
              {hasLiveAnalytics
                ? 'Revenue signals are stable, risk is concentrated in a small segment, and the strongest opportunity remains in retention-led expansion plays.'
                : 'The dashboard is fetching real customer, churn, and engagement data from the backend.'}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3 min-w-[280px]">
            <div className="metric-pill">
              <span className="metric-label">Risk score</span>
              <strong>{hasLiveAnalytics ? (highRiskCount || 0).toLocaleString() : 'N/A'}</strong>
            </div>
            <div className="metric-pill">
              <span className="metric-label">Retention</span>
              <strong>{hasLiveAnalytics ? `${(100 - ((highRiskCount / Math.max(totalCustomers || 1, 1)) * 100)).toFixed(1)}%` : 'N/A'}</strong>
            </div>
            <div className="metric-pill">
              <span className="metric-label">Engagement</span>
              <strong>{hasLiveAnalytics ? `${(Number(engagementStats.avg_engagement) || 0).toFixed(1)}%` : 'N/A'}</strong>
            </div>
            <div className="metric-pill">
              <span className="metric-label">LTV</span>
              <strong>{hasLiveAnalytics ? `$${(Number(ltvStats.predicted_ltv) || 0).toLocaleString()}` : 'N/A'}</strong>
            </div>
          </div>
        </div>
      </div>

      {/* AI Action Board */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <FiZap className="text-indigo-500" /> AI Action Board
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {aiActions.map((action) => (
            <div key={action.title} className={`rounded-xl border-l-4 p-4 ${action.tone}`}>
              <p className="text-sm font-semibold mb-2">{action.title}</p>
              <p className="text-sm leading-relaxed">{action.description}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Executive Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="rounded-xl border border-indigo-100 bg-indigo-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Revenue at Risk</p>
            <p className="mt-2 text-2xl font-bold text-indigo-900">
              ${((Number(ltvStats.predicted_ltv) || 0) * Math.max(0.05, (highRiskCount / Math.max(Number(engagementStats.total_customers) || 1, 1)))).toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </p>
            <p className="mt-1 text-xs text-indigo-700">based on churn exposure</p>
          </div>

          <div className="rounded-xl border border-emerald-100 bg-emerald-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-emerald-600">VIP Share</p>
            <p className="mt-2 text-2xl font-bold text-emerald-900">
              {(() => {
                const vipCustomers = analytics.segmentation?.find((s) => s.segment === 'VIP')?.count || 0;
                const total = Number(engagementStats.total_customers) || 0;
                return total ? `${((vipCustomers / total) * 100).toFixed(1)}%` : '0.0%';
              })()}
            </p>
            <p className="mt-1 text-xs text-emerald-700">high-value customer concentration</p>
          </div>

          <div className="rounded-xl border border-amber-100 bg-amber-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-600">Retention Index</p>
            <p className="mt-2 text-2xl font-bold text-amber-900">
              {(() => {
                const total = Number(engagementStats.total_customers) || 0;
                const retention = total ? 100 - ((highRiskCount / total) * 100) : 100;
                return `${Math.max(0, retention).toFixed(1)}%`;
              })()}
            </p>
            <p className="mt-1 text-xs text-amber-700">customer stability outlook</p>
          </div>

          <div className="rounded-xl border border-rose-100 bg-rose-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-rose-600">Risk Pressure</p>
            <p className="mt-2 text-2xl font-bold text-rose-900">
              {analytics.churn?.find((c) => c.risk_level === 'HIGH')?.percentage || 0}%
            </p>
            <p className="mt-1 text-xs text-rose-700">high-risk customer share</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Priority Risk Matrix</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { label: 'Immediate', value: analytics.churn?.find((c) => c.risk_level === 'HIGH')?.count || 0, tone: 'bg-red-50 border-red-200 text-red-700', detail: 'requires outreach sequencing' },
            { label: 'Monitor', value: analytics.churn?.find((c) => c.risk_level === 'MEDIUM')?.count || 0, tone: 'bg-yellow-50 border-yellow-200 text-yellow-700', detail: 'watch for drop-offs' },
            { label: 'Healthy', value: analytics.churn?.find((c) => c.risk_level === 'LOW')?.count || 0, tone: 'bg-green-50 border-green-200 text-green-700', detail: 'retain and upsell' },
          ].map((item) => (
            <div key={item.label} className={`rounded-xl border p-4 ${item.tone}`}>
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold uppercase tracking-wide">{item.label}</p>
                <span className="text-2xl font-bold">{item.value}</span>
              </div>
              <p className="mt-3 text-xs opacity-80">{item.detail}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Forecast & Growth Momentum</h3>
        {(() => {
          const baseEngagement = Number(engagementStats.avg_engagement) || 0;
          const baseLtv = Number(ltvStats.predicted_ltv) || 0;
          const forecastData = [
            { month: 'Jan', engagement: Math.max(20, baseEngagement - 8), ltv: Math.max(200, baseLtv * 0.72) },
            { month: 'Feb', engagement: Math.max(25, baseEngagement - 5), ltv: Math.max(260, baseLtv * 0.8) },
            { month: 'Mar', engagement: Math.max(30, baseEngagement - 2), ltv: Math.max(330, baseLtv * 0.9) },
            { month: 'Apr', engagement: baseEngagement, ltv: baseLtv },
            { month: 'May', engagement: Math.min(100, baseEngagement + 8), ltv: baseLtv * 1.15 },
            { month: 'Jun', engagement: Math.min(100, baseEngagement + 14), ltv: baseLtv * 1.28 },
          ];

          return (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={forecastData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="engagement" fill="#3B82F6" radius={[8, 8, 0, 0]} name="Engagement %" />
                <Bar dataKey="ltv" fill="#10B981" radius={[8, 8, 0, 0]} name="Predicted LTV" />
              </BarChart>
            </ResponsiveContainer>
          );
        })()}
      </div>

      {/* Export Toolbar */}
      <div className="flex justify-end gap-3">
        <button
          onClick={handleExportCustomers}
          className="flex items-center gap-2 px-4 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
        >
          <FiDownload /> Export Customers CSV
        </button>
        <button
          onClick={handleExportCustomersXlsx}
          className="flex items-center gap-2 px-4 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
        >
          <FiDownload /> Export Customers Excel
        </button>
        <button
          onClick={handleExportReport}
          className="flex items-center gap-2 px-4 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
        >
          <FiDownload /> Export Report CSV
        </button>
        <button
          onClick={handleExportReportPdf}
          className="flex items-center gap-2 px-4 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
        >
          <FiDownload /> Export Report PDF
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Total Customers</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {Number(engagementStats.total_customers) || 0}
              </p>
            </div>
            <FiUsers className="text-blue-500 text-3xl opacity-20" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Engagement Score</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {(Number(engagementStats.avg_engagement) || 0).toFixed(1)}%
              </p>
            </div>
            <FiTrendingUp className="text-green-500 text-3xl opacity-20" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Churn Risk</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {highRiskCount}
              </p>
            </div>
            <FiAlertTriangle className="text-red-500 text-3xl opacity-20" />
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Customer Segmentation Pie Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Customer Segmentation</h3>
          {analytics.segmentation?.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={analytics.segmentation}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="count"
                  nameKey="segment"
                >
                  {analytics.segmentation.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No data available</p>
          )}
        </div>

        {/* Engagement Metrics Bar Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Engagement Metrics</h3>
          {engagementMetricsData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={engagementMetricsData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="metric" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3B82F6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No data available</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Customer Health Profile</h3>
          {engagementProfileData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <RadarChart data={engagementProfileData}>
                <PolarGrid stroke="#e5e7eb" />
                <PolarAngleAxis dataKey="metric" tick={{ fill: '#475569', fontSize: 12 }} />
                <PolarRadiusAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 10 }} />
                <Radar name="Health" dataKey="value" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.4} />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No engagement profile available</p>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Customer Lifetime Value Predictions</h3>
          {ltvChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={ltvChartData}>
                <defs>
                  <linearGradient id="actualLtv" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0.2} />
                  </linearGradient>
                  <linearGradient id="predictedLtv" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.7} />
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0.2} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="Actual LTV" stroke="#8B5CF6" fill="url(#actualLtv)" />
                <Area type="monotone" dataKey="Predicted LTV" stroke="#10B981" fill="url(#predictedLtv)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No LTV data available</p>
          )}
        </div>
      </div>

      {/* Churn Risk Analysis */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Churn Risk Distribution</h3>
        {riskDistributionData.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ResponsiveContainer width="100%" height={270}>
              <BarChart data={riskDistributionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                  {riskDistributionData.map((entry, index) => (
                    <Cell
                      key={`risk-${index}`}
                      fill={
                        entry.name === 'HIGH' ? '#EF4444' :
                        entry.name === 'MEDIUM' ? '#F59E0B' : '#10B981'
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-gray-200">
                  <tr>
                    <th className="text-left py-2 px-4 font-semibold text-gray-900">Risk Level</th>
                    <th className="text-left py-2 px-4 font-semibold text-gray-900">Customers</th>
                    <th className="text-left py-2 px-4 font-semibold text-gray-900">Percentage</th>
                    <th className="text-left py-2 px-4 font-semibold text-gray-900">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {riskDistributionData.map((item, idx) => (
                    <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 text-sm text-gray-900">{item.name}</td>
                      <td className="py-3 px-4 text-sm text-gray-600">{item.count}</td>
                      <td className="py-3 px-4 text-sm text-gray-600">{item.percentage}%</td>
                      <td className="py-3 px-4 text-sm">
                        <span className={
                          item.name === 'HIGH'
                            ? 'text-red-500 font-medium'
                            : item.name === 'MEDIUM'
                            ? 'text-yellow-600 font-medium'
                            : 'text-green-600 font-medium'
                        }>
                          {item.name === 'HIGH' ? '⚠️ High Risk' : item.name === 'MEDIUM' ? '● Medium Risk' : '✓ Low Risk'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">No churn risk data available</p>
        )}
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
