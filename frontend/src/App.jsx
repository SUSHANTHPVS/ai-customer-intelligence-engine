import React, { useState, useEffect } from 'react';
import { FiMenu, FiX, FiBarChart2, FiTrendingUp, FiSettings, FiLogOut, FiUsers, FiActivity, FiDatabase, FiGrid } from 'react-icons/fi';
import { apiClient } from './api/client';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import ModelMetricsDashboard from './components/ModelMetricsDashboard';
import CustomerExplorer from './components/CustomerExplorer';
import LiveActivityFeed from './components/LiveActivityFeed';
import SettingsPage from './components/SettingsPage';
import DatasetManager from './components/DatasetManager';
import CohortAnalysis from './components/CohortAnalysis';
import NotificationBell from './components/NotificationBell';
import Login from './components/Login';
import { HealthStatus, RefreshButton } from './components/HealthStatus';
import useDashboardStore from './store/dashboardStore';
import useAuthStore from './store/authStore';
import useThemeStore from './store/themeStore';
import useDatasetStore from './store/datasetStore';
import './App.css';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('analytics');
  const [preferences, setPreferences] = useState({});
  const { error, lastUpdated } = useDashboardStore();
  const { user, accessToken, logout } = useAuthStore();
  const { refresh: refreshDatasets, getActiveDatasetName } = useDatasetStore();
  useThemeStore(); // ensures the store (and persisted theme class) is initialized

  useEffect(() => {
    if (accessToken) refreshDatasets();
  }, [accessToken, refreshDatasets]);

  useEffect(() => {
    if (!accessToken) return;

    const loadPreferences = async () => {
      try {
        const { data } = await apiClient.auth.getPreferences();
        setPreferences(data.preferences || {});
      } catch {
        setPreferences({});
      }
    };

    loadPreferences();
  }, [accessToken]);

  useEffect(() => {
    const handlePreferencesUpdated = (event) => {
      setPreferences((prev) => ({ ...prev, ...event.detail }));
    };

    window.addEventListener('preferences-updated', handlePreferencesUpdated);
    return () => window.removeEventListener('preferences-updated', handlePreferencesUpdated);
  }, []);

  useEffect(() => {
    if (!accessToken || !(preferences.autoRefresh ?? true)) return;

    const refreshLoop = setInterval(() => {
      useDashboardStore.getState().refreshAll();
    }, 60000);

    return () => clearInterval(refreshLoop);
  }, [accessToken, preferences.autoRefresh]);

  if (!accessToken) {
    return <Login />;
  }

  const tabs = [
    { id: 'analytics', label: 'Analytics', icon: FiBarChart2 },
    { id: 'customers', label: 'Customers', icon: FiUsers },
    { id: 'cohorts', label: 'Cohorts', icon: FiGrid },
    { id: 'live', label: 'Live Feed', icon: FiActivity },
    { id: 'models', label: 'Model Metrics', icon: FiTrendingUp },
    { id: 'datasets', label: 'Datasets', icon: FiDatabase },
    { id: 'settings', label: 'Settings', icon: FiSettings },
  ];

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? 'w-64' : 'w-20'
        } bg-gray-900 text-white transition-all duration-300 flex flex-col`}
      >
        {/* Logo */}
        <div className="p-6 border-b border-gray-800 flex items-center justify-between">
          {sidebarOpen && (
            <h1 className="text-xl font-bold">Customer Intelligence</h1>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1 hover:bg-gray-800 rounded transition-colors"
          >
            {sidebarOpen ? <FiX size={24} /> : <FiMenu size={24} />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-4 px-4 py-3 rounded-lg transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`}
              >
                <Icon size={20} />
                {sidebarOpen && <span>{tab.label}</span>}
              </button>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-800 space-y-2">
          {sidebarOpen && user && (
            <p className="px-4 text-xs text-gray-500 truncate">Signed in as {user.username}</p>
          )}
          <button
            onClick={logout}
            className="w-full flex items-center gap-4 px-4 py-3 rounded-lg text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
          >
            <FiLogOut size={20} />
            {sidebarOpen && <span>Logout</span>}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header */}
        <header className="bg-white shadow-md border-b border-gray-200 px-8 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {tabs.find(t => t.id === activeTab)?.label}
            </h2>
            <div className="flex items-center gap-2 mt-1">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-blue-50 text-blue-700 rounded-full">
                <FiDatabase size={12} /> {getActiveDatasetName()}
              </span>
              {lastUpdated && (
                <p className="text-sm text-gray-600">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                </p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <NotificationBell />
            <RefreshButton />
          </div>
        </header>

        {/* Error Banner */}
        {error && (
          <div className="bg-red-50 border-b border-red-200 px-8 py-3 flex items-center gap-3">
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800">{error}</p>
            </div>
            <button
              onClick={() => useDashboardStore.setState({ error: null })}
              className="text-red-600 hover:text-red-800"
            >
              ✕
            </button>
          </div>
        )}

        {/* Content Area */}
        <main
          className="flex-1 overflow-auto px-8 py-6"
          style={preferences.compactLayout ? { padding: '1rem' } : undefined}
        >
          {/* Health Status Card */}
          <div className="mb-6">
            <HealthStatus />
          </div>

          {/* Tab Content */}
          {activeTab === 'analytics' && <AnalyticsDashboard />}
          {activeTab === 'customers' && <CustomerExplorer />}
          {activeTab === 'cohorts' && <CohortAnalysis showEmptyLabels={preferences.showEmptyLabels ?? true} />}
          {activeTab === 'live' && <LiveActivityFeed />}
          {activeTab === 'models' && <ModelMetricsDashboard />}
          {activeTab === 'datasets' && <DatasetManager />}
          {activeTab === 'settings' && <SettingsPage />}
        </main>
      </div>
    </div>
  );
}

export default App;
