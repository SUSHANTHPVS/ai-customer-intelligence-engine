import React, { useEffect, useState } from 'react';
import { FiMoon, FiSun, FiKey, FiTrash2, FiPlus, FiFileText, FiShield, FiLink, FiExternalLink, FiSend } from 'react-icons/fi';
import useThemeStore from '../store/themeStore';
import useAuthStore from '../store/authStore';
import { apiClient } from '../api/client';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const SettingsPage = () => {
  const { darkMode, toggleDarkMode } = useThemeStore();
  const { user } = useAuthStore();
  const isAdmin = user?.role === 'admin';

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Appearance</h3>
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-gray-900 dark:text-white">Dark Mode</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Switch between light and dark themes</p>
          </div>
          <button
            onClick={toggleDarkMode}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            {darkMode ? <FiSun /> : <FiMoon />}
            {darkMode ? 'Light Mode' : 'Dark Mode'}
          </button>
        </div>
      </div>

      <TwoFactorSettings />

      {isAdmin && <ApiKeyManager />}
      {isAdmin && <WebhookManager />}
      {isAdmin && <AuditLogViewer />}
      {isAdmin && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <FiLink /> Developer Tools
          </h3>
          <a
            href={`${API_URL}/graphql`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            <FiExternalLink /> Open GraphQL Playground
          </a>
        </div>
      )}
    </div>
  );
};

const TwoFactorSettings = () => {
  const [enabled, setEnabled] = useState(false);
  const [setupData, setSetupData] = useState(null);
  const [code, setCode] = useState('');
  const [message, setMessage] = useState(null);

  const loadStatus = async () => {
    const { data } = await apiClient.twoFactor.getStatus();
    setEnabled(data.enabled);
  };

  useEffect(() => { loadStatus(); }, []);

  const handleSetup = async () => {
    setMessage(null);
    const { data } = await apiClient.twoFactor.setup();
    setSetupData(data);
  };

  const handleEnable = async () => {
    try {
      await apiClient.twoFactor.enable(code);
      setSetupData(null);
      setCode('');
      setMessage({ type: 'success', text: '2FA enabled successfully.' });
      await loadStatus();
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.error || 'Invalid code' });
    }
  };

  const handleDisable = async () => {
    await apiClient.twoFactor.disable();
    setMessage({ type: 'success', text: '2FA disabled.' });
    await loadStatus();
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
        <FiShield /> Two-Factor Authentication
      </h3>

      {message && (
        <p className={`text-sm mb-3 ${message.type === 'error' ? 'text-red-600' : 'text-green-600'}`}>{message.text}</p>
      )}

      {enabled ? (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600 dark:text-gray-300">2FA is currently <span className="font-semibold text-green-600">enabled</span> on your account.</p>
          <button onClick={handleDisable} className="px-4 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 text-sm font-medium">
            Disable 2FA
          </button>
        </div>
      ) : setupData ? (
        <div className="space-y-4">
          <p className="text-sm text-gray-600 dark:text-gray-300">Scan this QR code with an authenticator app (Google Authenticator, Authy), then enter the 6-digit code below.</p>
          <img src={setupData.qr_code} alt="2FA QR code" className="w-40 h-40 border border-gray-200 rounded-lg" />
          <p className="text-xs text-gray-400 font-mono break-all">Manual entry key: {setupData.secret}</p>
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="000000"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              maxLength={6}
              className="px-4 py-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:text-white dark:border-gray-600"
            />
            <button onClick={handleEnable} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
              Verify & Enable
            </button>
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600 dark:text-gray-300">Add an extra layer of security to your account.</p>
          <button onClick={handleSetup} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium">
            Set Up 2FA
          </button>
        </div>
      )}
    </div>
  );
};

const WebhookManager = () => {
  const [webhooks, setWebhooks] = useState([]);
  const [newUrl, setNewUrl] = useState('');
  const [revealedSecret, setRevealedSecret] = useState(null);

  const loadWebhooks = async () => {
    const { data } = await apiClient.admin.listWebhooks();
    setWebhooks(data.webhooks || []);
  };

  useEffect(() => { loadWebhooks(); }, []);

  const handleCreate = async () => {
    if (!newUrl.trim()) return;
    const { data } = await apiClient.admin.createWebhook(newUrl.trim());
    setRevealedSecret(data.secret);
    setNewUrl('');
    await loadWebhooks();
  };

  const handleDelete = async (id) => {
    await apiClient.admin.deleteWebhook(id);
    await loadWebhooks();
  };

  const handleTest = async (id) => {
    await apiClient.admin.testWebhook(id);
    await loadWebhooks();
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
        <FiLink /> Webhook Integrations
      </h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
        Receive an HMAC-signed HTTP POST whenever a HIGH churn-risk customer is detected.
      </p>

      {revealedSecret && (
        <div className="mb-4 bg-yellow-50 border border-yellow-300 rounded-lg p-3 text-sm">
          <p className="font-semibold text-yellow-800">Webhook signing secret (save it now):</p>
          <code className="block mt-1 break-all bg-white px-2 py-1 rounded border border-yellow-200">{revealedSecret}</code>
        </div>
      )}

      <div className="flex gap-3 mb-4">
        <input
          type="text"
          placeholder="https://example.com/webhooks/churn-risk"
          value={newUrl}
          onChange={(e) => setNewUrl(e.target.value)}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:text-white dark:border-gray-600"
        />
        <button onClick={handleCreate} className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
          <FiPlus /> Add Webhook
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b border-gray-200 dark:border-gray-700">
            <tr>
              <th className="text-left py-2 px-3 font-semibold text-gray-900 dark:text-white">URL</th>
              <th className="text-left py-2 px-3 font-semibold text-gray-900 dark:text-white">Last Status</th>
              <th className="text-left py-2 px-3 font-semibold text-gray-900 dark:text-white">Last Triggered</th>
              <th className="text-left py-2 px-3"></th>
            </tr>
          </thead>
          <tbody>
            {webhooks.map((w) => (
              <tr key={w.id} className="border-b border-gray-100 dark:border-gray-700">
                <td className="py-2 px-3 text-gray-900 dark:text-white truncate max-w-xs">{w.url}</td>
                <td className="py-2 px-3 text-gray-500 dark:text-gray-400 truncate max-w-xs">{w.last_status || '—'}</td>
                <td className="py-2 px-3 text-gray-400">{w.last_triggered_at ? new Date(w.last_triggered_at).toLocaleString() : 'Never'}</td>
                <td className="py-2 px-3 flex gap-3">
                  <button onClick={() => handleTest(w.id)} className="text-blue-500 hover:text-blue-700" title="Send test payload">
                    <FiSend />
                  </button>
                  <button onClick={() => handleDelete(w.id)} className="text-red-500 hover:text-red-700" title="Delete">
                    <FiTrash2 />
                  </button>
                </td>
              </tr>
            ))}
            {webhooks.length === 0 && (
              <tr><td colSpan={4} className="text-center py-6 text-gray-400">No webhooks configured</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const ApiKeyManager = () => {
  const [keys, setKeys] = useState([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [revealedKey, setRevealedKey] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadKeys = async () => {
    const { data } = await apiClient.admin.listApiKeys();
    setKeys(data.api_keys || []);
  };

  useEffect(() => { loadKeys(); }, []);

  const handleCreate = async () => {
    if (!newKeyName.trim()) return;
    setLoading(true);
    try {
      const { data } = await apiClient.admin.createApiKey(newKeyName.trim());
      setRevealedKey(data.api_key);
      setNewKeyName('');
      await loadKeys();
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = async (id) => {
    await apiClient.admin.revokeApiKey(id);
    await loadKeys();
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
        <FiKey /> API Key Management
      </h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
        Keys grant access to the external <code>/api/v1/predict/*</code> ML prediction endpoints.
      </p>

      {revealedKey && (
        <div className="mb-4 bg-yellow-50 border border-yellow-300 rounded-lg p-3 text-sm">
          <p className="font-semibold text-yellow-800">Copy this key now — it won't be shown again:</p>
          <code className="block mt-1 break-all bg-white px-2 py-1 rounded border border-yellow-200">{revealedKey}</code>
        </div>
      )}

      <div className="flex gap-3 mb-4">
        <input
          type="text"
          placeholder="Key name (e.g. billing-integration)"
          value={newKeyName}
          onChange={(e) => setNewKeyName(e.target.value)}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:text-white dark:border-gray-600"
        />
        <button
          onClick={handleCreate}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg"
        >
          <FiPlus /> Create Key
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b border-gray-200 dark:border-gray-700">
            <tr>
              <th className="text-left py-2 px-3 font-semibold text-gray-900 dark:text-white">Name</th>
              <th className="text-left py-2 px-3 font-semibold text-gray-900 dark:text-white">Prefix</th>
              <th className="text-left py-2 px-3 font-semibold text-gray-900 dark:text-white">Created By</th>
              <th className="text-left py-2 px-3 font-semibold text-gray-900 dark:text-white">Status</th>
              <th className="text-left py-2 px-3"></th>
            </tr>
          </thead>
          <tbody>
            {keys.map((k) => (
              <tr key={k.id} className="border-b border-gray-100 dark:border-gray-700">
                <td className="py-2 px-3 text-gray-900 dark:text-white">{k.name}</td>
                <td className="py-2 px-3 font-mono text-gray-500 dark:text-gray-400">{k.key_prefix}...</td>
                <td className="py-2 px-3 text-gray-500 dark:text-gray-400">{k.created_by}</td>
                <td className="py-2 px-3">
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${k.revoked ? 'bg-gray-200 text-gray-600' : 'bg-green-100 text-green-800'}`}>
                    {k.revoked ? 'Revoked' : 'Active'}
                  </span>
                </td>
                <td className="py-2 px-3">
                  {!k.revoked && (
                    <button onClick={() => handleRevoke(k.id)} className="text-red-500 hover:text-red-700">
                      <FiTrash2 />
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {keys.length === 0 && (
              <tr><td colSpan={5} className="text-center py-6 text-gray-400">No API keys yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const AuditLogViewer = () => {
  const [logs, setLogs] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    const load = async () => {
      const { data } = await apiClient.admin.getAuditLog({ page, page_size: 10 });
      setLogs(data.results || []);
      setTotalPages(data.total_pages || 1);
    };
    load();
  }, [page]);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
        <FiFileText /> Audit Log
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b border-gray-200 dark:border-gray-700">
            <tr>
              <th className="text-left py-2 px-3 font-semibold text-gray-900 dark:text-white">User</th>
              <th className="text-left py-2 px-3 font-semibold text-gray-900 dark:text-white">Action</th>
              <th className="text-left py-2 px-3 font-semibold text-gray-900 dark:text-white">Detail</th>
              <th className="text-left py-2 px-3 font-semibold text-gray-900 dark:text-white">When</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id} className="border-b border-gray-100 dark:border-gray-700">
                <td className="py-2 px-3 text-gray-900 dark:text-white">{log.username || '—'}</td>
                <td className="py-2 px-3 text-gray-700 dark:text-gray-300">{log.action}</td>
                <td className="py-2 px-3 text-gray-500 dark:text-gray-400 truncate max-w-xs">{log.detail}</td>
                <td className="py-2 px-3 text-gray-400">{new Date(log.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {logs.length === 0 && (
              <tr><td colSpan={4} className="text-center py-6 text-gray-400">No audit events yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between mt-4">
        <button
          disabled={page <= 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          className="px-4 py-2 text-sm bg-gray-100 dark:bg-gray-700 dark:text-white rounded-lg disabled:opacity-50"
        >
          Previous
        </button>
        <span className="text-sm text-gray-600 dark:text-gray-400">Page {page} of {totalPages}</span>
        <button
          disabled={page >= totalPages}
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          className="px-4 py-2 text-sm bg-gray-100 dark:bg-gray-700 dark:text-white rounded-lg disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default SettingsPage;
