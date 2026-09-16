import { create } from 'zustand';
import { apiClient } from '../api/client';

export const useDashboardStore = create((set, get) => ({
  // State
  loading: false,
  error: null,
  apiHealth: null,
  analytics: {
    segmentation: [],
    engagement: {},
    ltv: {},
    churn: [],
  },
  models: {
    metrics: {},
    performance: [],
    leaderboard: [],
  },
  insight: null,
  lastUpdated: null,

  // Actions
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),

  checkHealth: async () => {
    try {
      const response = await apiClient.health.check();
      set({ apiHealth: response.data });
      return true;
    } catch (error) {
      set({ error: 'Failed to connect to API', apiHealth: null });
      return false;
    }
  },

  fetchAnalytics: async () => {
    set({ loading: true, error: null });
    try {
      const [segmentation, engagement, ltv, churn] = await Promise.all([
        apiClient.analytics.getCustomerSegmentation(),
        apiClient.analytics.getEngagementMetrics(),
        apiClient.analytics.getLTVPredictions(),
        apiClient.analytics.getChurnRisk(),
      ]);

      set({
        analytics: {
          segmentation: segmentation.data.segments || [],
          engagement: engagement.data || {},
          ltv: ltv.data || {},
          churn: churn.data.churn_risk || [],
        },
        lastUpdated: new Date(),
        loading: false,
      });
    } catch (error) {
      set({
        error: error.message || 'Failed to fetch analytics',
        loading: false,
      });
    }
  },

  fetchModelMetrics: async () => {
    set({ loading: true, error: null });
    try {
      const [metrics, performance, leaderboard] = await Promise.all([
        apiClient.models.getModelMetrics(),
        apiClient.models.getModelPerformance(),
        apiClient.models.getModelLeaderboard(),
      ]);

      set({
        models: {
          metrics: metrics.data || {},
          performance: performance.data.performance_history || [],
          leaderboard: leaderboard.data.leaderboard || [],
        },
        loading: false,
      });
    } catch (error) {
      set({
        error: error.message || 'Failed to fetch model metrics',
        loading: false,
      });
    }
  },

  // Picks a single random insight out of the full generated pool — a fresh one
  // is drawn every time this runs (page load, Refresh button, dataset switch).
  fetchInsight: async () => {
    try {
      const { data } = await apiClient.analytics.getInsights();
      const pool = data.insights || [];
      const picked = pool.length > 0 ? pool[Math.floor(Math.random() * pool.length)] : null;
      set({ insight: picked });
    } catch (error) {
      set({ insight: null });
    }
  },

  refreshAll: async () => {
    const health = await get().checkHealth();
    if (health) {
      await Promise.all([get().fetchAnalytics(), get().fetchModelMetrics(), get().fetchInsight()]);
    }
  },
}));

export default useDashboardStore;
