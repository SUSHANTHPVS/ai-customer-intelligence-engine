import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const client = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for auth token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor for error handling + silent token refresh
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry && originalRequest.url !== '/auth/login') {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        originalRequest._retry = true;
        try {
          const { data } = await axios.post(`${API_URL}/auth/refresh`, {}, {
            headers: { Authorization: `Bearer ${refreshToken}` },
          });
          localStorage.setItem('auth_token', data.access_token);
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
          return client(originalRequest);
        } catch (refreshError) {
          localStorage.removeItem('auth_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('auth_user');
          window.location.href = '/';
          return Promise.reject(refreshError);
        }
      }

      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('auth_user');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export const apiClient = {
  // Analytics endpoints
  analytics: {
    getCustomerSegmentation: () => client.get('/analytics/customer-segmentation'),
    getEngagementMetrics: () => client.get('/analytics/engagement-metrics'),
    getLTVPredictions: () => client.get('/analytics/ltv-predictions'),
    getChurnRisk: () => client.get('/analytics/churn-risk'),
    getInsights: () => client.get('/analytics/insights'),
    getCohortRetention: () => client.get('/analytics/cohort-retention'),
  },

  // Model endpoints
  models: {
    getModelMetrics: () => client.get('/models/metrics'),
    getModelPerformance: () => client.get('/models/performance'),
    retrainModel: (modelName) => client.post(`/models/${modelName}/retrain`),
  },

  // Customer 360 search & profile
  customers: {
    search: (params) => client.get('/customers/search', { params }),
    getProfile: (customerId) => client.get(`/customers/${encodeURIComponent(customerId)}/profile`),
    importCsv: (file) => {
      const formData = new FormData();
      formData.append('file', file);
      return client.post('/customers/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
  },

  // CSV/PDF/Excel exports
  export: {
    customers: (params) => client.get('/export/customers.csv', { params, responseType: 'blob' }),
    customersXlsx: (params) => client.get('/export/customers.xlsx', { params, responseType: 'blob' }),
    analyticsReport: () => client.get('/export/analytics-report.csv', { responseType: 'blob' }),
    analyticsReportPdf: () => client.get('/export/analytics-report.pdf', { responseType: 'blob' }),
  },

  // Background job status
  jobs: {
    getStatus: () => client.get('/jobs/status'),
  },

  // Multi-tenant dataset management (upload your own CSVs, isolated per user)
  datasets: {
    list: () => client.get('/datasets'),
    status: (id) => client.get(`/datasets/${id}/status`),
    activate: (id) => client.post(`/datasets/${id}/activate`),
    remove: (id) => client.delete(`/datasets/${id}`),
    upload: (formData) => client.post('/datasets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
    trainModel: (id) => client.post(`/datasets/${id}/train`),
    getModel: (id) => client.get(`/datasets/${id}/model`),
    detectAnomalies: (id) => client.post(`/datasets/${id}/detect-anomalies`),
    getAnomalies: (id) => client.get(`/datasets/${id}/anomalies`),
    regenerateQualityReport: (id) => client.post(`/datasets/${id}/quality-report`),
  },

  // Admin: API key management + audit log (requires 'admin' role)
  admin: {
    listApiKeys: () => client.get('/admin/api-keys'),
    createApiKey: (name) => client.post('/admin/api-keys', { name }),
    revokeApiKey: (id) => client.delete(`/admin/api-keys/${id}`),
    getAuditLog: (params) => client.get('/admin/audit-log', { params }),
    listWebhooks: () => client.get('/admin/webhooks'),
    createWebhook: (url) => client.post('/admin/webhooks', { url }),
    deleteWebhook: (id) => client.delete(`/admin/webhooks/${id}`),
    testWebhook: (id) => client.post(`/admin/webhooks/${id}/test`),
  },

  // Two-factor authentication
  twoFactor: {
    getStatus: () => client.get('/auth/2fa/status'),
    setup: () => client.post('/auth/2fa/setup'),
    enable: (code) => client.post('/auth/2fa/enable', { code }),
    disable: () => client.post('/auth/2fa/disable'),
  },

  // Health check
  health: {
    check: () => client.get('/health'),
  },
};

export default client;
