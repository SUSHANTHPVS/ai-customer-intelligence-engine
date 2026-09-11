import React, { useEffect } from 'react';
import useDashboardStore from '../store/dashboardStore';
import { PieChart, Pie, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
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

      {/* LTV Predictions Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Customer Lifetime Value Predictions</h3>
        {ltvChartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={ltvChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="Actual LTV" fill="#8B5CF6" radius={[8, 8, 0, 0]} />
              <Bar dataKey="Predicted LTV" fill="#10B981" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-500 text-center py-8">No LTV data available</p>
        )}
      </div>

      {/* Churn Risk Analysis */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Churn Risk Distribution</h3>
        {analytics.churn?.length > 0 ? (
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
                {analytics.churn.map((item, idx) => (
                  <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm text-gray-900">{item.risk_level}</td>
                    <td className="py-3 px-4 text-sm text-gray-600">{item.count}</td>
                    <td className="py-3 px-4 text-sm text-gray-600">{item.percentage}%</td>
                    <td className="py-3 px-4 text-sm">
                      <span className={
                        item.risk_level === 'HIGH'
                          ? 'text-red-500 font-medium'
                          : item.risk_level === 'MEDIUM'
                          ? 'text-yellow-600 font-medium'
                          : 'text-green-600 font-medium'
                      }>
                        {item.risk_level === 'HIGH' ? '⚠️ High Risk' : item.risk_level === 'MEDIUM' ? '● Medium Risk' : '✓ Low Risk'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">No churn risk data available</p>
        )}
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
