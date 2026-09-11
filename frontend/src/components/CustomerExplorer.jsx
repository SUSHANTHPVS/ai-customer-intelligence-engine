import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FiSearch, FiX, FiUser, FiMail, FiGlobe, FiTrendingUp, FiUpload, FiCompass } from 'react-icons/fi';
import { apiClient } from '../api/client';
import useAuthStore from '../store/authStore';

const SEGMENTS = ['', 'VIP', 'STANDARD', 'AT_RISK'];
const RISK_LEVELS = ['', 'HIGH', 'MEDIUM', 'LOW'];

const badgeColor = (value, kind) => {
  if (kind === 'segment') {
    if (value === 'VIP') return 'bg-purple-100 text-purple-800';
    if (value === 'AT_RISK') return 'bg-red-100 text-red-800';
    return 'bg-blue-100 text-blue-800';
  }
  if (value === 'HIGH') return 'bg-red-100 text-red-800';
  if (value === 'MEDIUM') return 'bg-yellow-100 text-yellow-800';
  return 'bg-green-100 text-green-800';
};

const CustomerExplorer = () => {
  const [query, setQuery] = useState('');
  const [segment, setSegment] = useState('');
  const [riskLevel, setRiskLevel] = useState('');
  const [page, setPage] = useState(1);
  const [results, setResults] = useState([]);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [importing, setImporting] = useState(false);
  const fileInputRef = useRef(null);
  const { user } = useAuthStore();
  const isAdmin = user?.role === 'admin';

  const runSearch = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.customers.search({
        q: query || undefined,
        segment: segment || undefined,
        risk_level: riskLevel || undefined,
        page,
        page_size: 10,
      });
      setResults(data.results || []);
      setTotalPages(data.total_pages || 1);
      setTotal(data.total || 0);
    } catch (error) {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [query, segment, riskLevel, page]);

  useEffect(() => {
    runSearch();
  }, [runSearch]);

  const openProfile = async (customerId) => {
    setProfileLoading(true);
    setSelectedProfile({ customer: { customer_id: customerId } });
    try {
      const { data } = await apiClient.customers.getProfile(customerId);
      setSelectedProfile(data);
    } catch (error) {
      setSelectedProfile(null);
    } finally {
      setProfileLoading(false);
    }
  };

  const handleFileSelected = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    setImportResult(null);
    try {
      const { data } = await apiClient.customers.importCsv(file);
      setImportResult(data);
      await runSearch();
    } catch (error) {
      setImportResult({ error: error.response?.data?.error || 'Import failed' });
    } finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-6">
      {isAdmin && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <FiUpload /> Bulk Customer Import
          </h3>
          <p className="text-sm text-gray-500 mb-4">
            Upload a CSV with columns: customer_id, first_name, last_name, email, country, industry, acquisition_channel, signup_date
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileSelected}
            disabled={importing}
            className="text-sm"
          />
          {importing && <p className="text-sm text-gray-500 mt-2">Importing...</p>}
          {importResult && !importResult.error && (
            <p className="text-sm text-green-700 mt-2">
              Inserted {importResult.inserted}, updated {importResult.updated}
              {importResult.total_errors > 0 && `, ${importResult.total_errors} row(s) skipped`}
            </p>
          )}
          {importResult?.error && (
            <p className="text-sm text-red-600 mt-2">{importResult.error}</p>
          )}
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Customer 360 Search</h3>
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-[220px]">
            <FiSearch className="absolute left-3 top-3 text-gray-400" />
            <input
              type="text"
              placeholder="Search by ID, name or email..."
              value={query}
              onChange={(e) => { setPage(1); setQuery(e.target.value); }}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            />
          </div>
          <select
            value={segment}
            onChange={(e) => { setPage(1); setSegment(e.target.value); }}
            className="px-4 py-2 border border-gray-300 rounded-lg"
          >
            {SEGMENTS.map((s) => (
              <option key={s} value={s}>{s || 'All Segments'}</option>
            ))}
          </select>
          <select
            value={riskLevel}
            onChange={(e) => { setPage(1); setRiskLevel(e.target.value); }}
            className="px-4 py-2 border border-gray-300 rounded-lg"
          >
            {RISK_LEVELS.map((r) => (
              <option key={r} value={r}>{r || 'All Risk Levels'}</option>
            ))}
          </select>
        </div>

        <p className="text-sm text-gray-500 mt-3">{total.toLocaleString()} customers found</p>

        <div className="overflow-x-auto mt-2">
          <table className="w-full">
            <thead className="border-b border-gray-200">
              <tr>
                <th className="text-left py-2 px-4 font-semibold text-gray-900">Customer</th>
                <th className="text-left py-2 px-4 font-semibold text-gray-900">Email</th>
                <th className="text-left py-2 px-4 font-semibold text-gray-900">Segment</th>
                <th className="text-left py-2 px-4 font-semibold text-gray-900">Risk</th>
                <th className="text-left py-2 px-4 font-semibold text-gray-900">LTV</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} className="text-center py-8 text-gray-500">Loading...</td></tr>
              ) : results.length === 0 ? (
                <tr><td colSpan={5} className="text-center py-8 text-gray-500">No customers match your filters</td></tr>
              ) : (
                results.map((c) => (
                  <tr
                    key={c.customer_id}
                    onClick={() => openProfile(c.customer_id)}
                    className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                  >
                    <td className="py-3 px-4 text-sm">
                      <p className="font-medium text-gray-900">{c.first_name} {c.last_name}</p>
                      <p className="text-gray-500">{c.customer_id}</p>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">{c.email}</td>
                    <td className="py-3 px-4 text-sm">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${badgeColor(c.segment, 'segment')}`}>
                        {c.segment || 'N/A'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${badgeColor(c.risk_level, 'risk')}`}>
                        {c.risk_level || 'N/A'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">
                      {c.lifetime_value ? `$${Number(c.lifetime_value).toFixed(2)}` : '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between mt-4">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="px-4 py-2 text-sm bg-gray-100 rounded-lg disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-600">Page {page} of {totalPages}</span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            className="px-4 py-2 text-sm bg-gray-100 rounded-lg disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>

      {/* Profile Drawer */}
      {selectedProfile && (
        <div className="fixed inset-0 bg-black/40 flex justify-end z-50" onClick={() => setSelectedProfile(null)}>
          <div className="w-full max-w-lg bg-white h-full overflow-y-auto p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-900">Customer Profile</h3>
              <button onClick={() => setSelectedProfile(null)} className="text-gray-400 hover:text-gray-700">
                <FiX size={24} />
              </button>
            </div>

            {profileLoading ? (
              <p className="text-gray-500">Loading profile...</p>
            ) : (
              <div className="space-y-6">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                    <FiUser className="text-blue-600" size={22} />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">
                      {selectedProfile.customer?.first_name} {selectedProfile.customer?.last_name}
                    </p>
                    <p className="text-sm text-gray-500">{selectedProfile.customer?.customer_id}</p>
                  </div>
                </div>

                <div className="space-y-2 text-sm">
                  <p className="flex items-center gap-2 text-gray-600"><FiMail /> {selectedProfile.customer?.email}</p>
                  <p className="flex items-center gap-2 text-gray-600"><FiGlobe /> {selectedProfile.customer?.country} • {selectedProfile.customer?.industry}</p>
                </div>

                <ProfileSection title="RFM & Lifetime Value" data={selectedProfile.rfm} />
                <ProfileSection title="Engagement" data={selectedProfile.engagement} />
                <ProfileSection title="Behavioral" data={selectedProfile.behavioral} />
                <ProfileSection title="Revenue" data={selectedProfile.revenue} />
                <ProfileSection title="Support" data={selectedProfile.support} />
                <ProfileSection title="Churn Risk" data={selectedProfile.churn_risk} highlight />

                {selectedProfile.recommendations?.length > 0 && (
                  <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                    <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                      <FiCompass size={14} /> Recommended Actions
                    </h4>
                    <ul className="space-y-2">
                      {selectedProfile.recommendations.map((rec, idx) => (
                        <li key={idx} className="text-sm flex items-start gap-2">
                          <span className={`mt-0.5 shrink-0 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${
                            rec.priority === 'high' ? 'bg-red-100 text-red-700' :
                            rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-green-100 text-green-700'
                          }`}>
                            {rec.priority}
                          </span>
                          <span className="text-gray-700">{rec.text}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const ProfileSection = ({ title, data, highlight }) => {
  if (!data) return null;
  const entries = Object.entries(data).filter(([key]) => !['customer_id', 'created_at', 'dataset_id'].includes(key));

  return (
    <div className={`rounded-lg border p-4 ${highlight ? 'border-red-200 bg-red-50' : 'border-gray-200'}`}>
      <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
        <FiTrendingUp size={14} /> {title}
      </h4>
      <dl className="grid grid-cols-2 gap-2 text-sm">
        {entries.map(([key, value]) => (
          <div key={key}>
            <dt className="text-gray-500">{key.replace(/_/g, ' ')}</dt>
            <dd className="font-medium text-gray-900">{String(value)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
};

export default CustomerExplorer;
