import React, { useEffect, useRef, useState } from 'react';
import { FiUploadCloud, FiCheckCircle, FiXCircle, FiClock, FiPlay, FiTrash2, FiDatabase, FiChevronDown, FiChevronUp, FiCpu, FiShield, FiAlertTriangle } from 'react-icons/fi';
import { apiClient } from '../api/client';
import useDatasetStore from '../store/datasetStore';
import useDashboardStore from '../store/dashboardStore';
import { reconnectSocket } from '../lib/socket';

const statusBadge = (status) => {
  if (status === 'ready') return 'bg-green-100 text-green-800';
  if (status === 'failed') return 'bg-red-100 text-red-800';
  return 'bg-yellow-100 text-yellow-800';
};

const completenessColor = (pct) => {
  if (pct >= 95) return 'text-green-600';
  if (pct >= 80) return 'text-yellow-600';
  return 'text-red-600';
};


const DatasetManager = () => {
  const { datasets, activeDatasetId, refresh } = useDatasetStore();
  const refreshDashboard = useDashboardStore((state) => state.refreshAll);
  const [name, setName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [processingId, setProcessingId] = useState(null);
  const [expandedId, setExpandedId] = useState(null);
  const [trainingId, setTrainingId] = useState(null);
  const [trainError, setTrainError] = useState(null);
  const [trainingAll, setTrainingAll] = useState(false);
  const [trainAllError, setTrainAllError] = useState(null);
  const [trainAllSummary, setTrainAllSummary] = useState(null);
  const [detectingId, setDetectingId] = useState(null);
  const [detectError, setDetectError] = useState(null);
  const [refreshingQualityId, setRefreshingQualityId] = useState(null);
  const [qualityError, setQualityError] = useState(null);
  const customersRef = useRef(null);
  const eventsRef = useRef(null);
  const transactionsRef = useRef(null);
  const supportRef = useRef(null);
  const pollRef = useRef(null);

  useEffect(() => {
    refresh();
    return () => clearInterval(pollRef.current);
  }, [refresh]);

  const pollStatus = (id) => {
    pollRef.current = setInterval(async () => {
      const { data } = await apiClient.datasets.status(id);
      if (data.status === 'ready' || data.status === 'failed') {
        clearInterval(pollRef.current);
        setProcessingId(null);
        refresh();
        if (data.status === 'ready') {
          reconnectSocket();
          await refreshDashboard();
        }
      }
    }, 3000);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    setUploadError(null);

    if (!customersRef.current?.files?.[0]) {
      setUploadError('customers.csv is required');
      return;
    }

    const formData = new FormData();
    if (name.trim()) formData.append('name', name.trim());
    formData.append('customers', customersRef.current.files[0]);
    if (eventsRef.current?.files?.[0]) formData.append('events', eventsRef.current.files[0]);
    if (transactionsRef.current?.files?.[0]) formData.append('transactions', transactionsRef.current.files[0]);
    if (supportRef.current?.files?.[0]) formData.append('support_tickets', supportRef.current.files[0]);

    setUploading(true);
    try {
      const { data } = await apiClient.datasets.upload(formData);
      setProcessingId(data.dataset_id);
      setName('');
      [customersRef, eventsRef, transactionsRef, supportRef].forEach((ref) => {
        if (ref.current) ref.current.value = '';
      });
      await refresh();
      pollStatus(data.dataset_id);
    } catch (error) {
      setUploadError(error.response?.data?.error || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleActivate = async (id) => {
    await apiClient.datasets.activate(id);
    await refresh();
    reconnectSocket();
    await refreshDashboard();
  };

  const handleDelete = async (id) => {
    await apiClient.datasets.remove(id);
    await refresh();
  };

  const handleTrainModel = async (id) => {
    setTrainError(null);
    setTrainingId(id);
    try {
      await apiClient.datasets.trainModel(id);
      await refresh();
    } catch (error) {
      setTrainError(error.response?.data?.error || 'Training failed');
    } finally {
      setTrainingId(null);
    }
  };

  const handleTrainAllModels = async () => {
    setTrainAllError(null);
    setTrainingAll(true);
    try {
      const { data } = await apiClient.datasets.trainAllModels();
      setTrainAllSummary(data);
      await refresh();
    } catch (error) {
      setTrainAllError(error.response?.data?.error || 'Training all models failed');
    } finally {
      setTrainingAll(false);
    }
  };

  const handleDetectAnomalies = async (id) => {
    setDetectError(null);
    setDetectingId(id);
    try {
      await apiClient.datasets.detectAnomalies(id);
      await refresh();
    } catch (error) {
      setDetectError(error.response?.data?.error || 'Anomaly detection failed');
    } finally {
      setDetectingId(null);
    }
  };

  const handleRegenerateQualityReport = async (id) => {
    setQualityError(null);
    setRefreshingQualityId(id);
    try {
      await apiClient.datasets.regenerateQualityReport(id);
      await refresh();
    } catch (error) {
      setQualityError(error.response?.data?.error || 'Failed to regenerate quality report');
    } finally {
      setRefreshingQualityId(null);
    }
  };

  const toggleExpanded = (id) => setExpandedId((prev) => (prev === id ? null : id));

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center gap-2">
          <FiUploadCloud /> Upload Your Own Dataset
        </h3>
        <p className="text-sm text-gray-500 mb-4">
          Upload your own CSV files to get a fully isolated analysis — Analytics, Customers, and Live Feed
          will all reflect your data once processing completes. <code>customers.csv</code> is required;
          the others are optional but improve feature accuracy.
        </p>

        {uploadError && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3">
            {uploadError}
          </div>
        )}

        <form onSubmit={handleUpload} className="space-y-4">
          <input
            type="text"
            placeholder="Dataset name (optional)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">customers.csv (required)</label>
              <input ref={customersRef} type="file" accept=".csv" className="text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">events.csv (optional)</label>
              <input ref={eventsRef} type="file" accept=".csv" className="text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">transactions.csv (optional)</label>
              <input ref={transactionsRef} type="file" accept=".csv" className="text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">support_tickets.csv (optional)</label>
              <input ref={supportRef} type="file" accept=".csv" className="text-sm" />
            </div>
          </div>

          <button
            type="submit"
            disabled={uploading || !!processingId}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg font-medium"
          >
            <FiUploadCloud /> {uploading ? 'Uploading...' : 'Upload & Process'}
          </button>

          {processingId && (
            <p className="text-sm text-yellow-700 flex items-center gap-2">
              <FiClock className="animate-spin" /> Processing dataset {processingId}... this can take a couple of minutes for larger files.
            </p>
          )}
        </form>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <FiDatabase /> Your Datasets
          </h3>
          <button
            onClick={handleTrainAllModels}
            disabled={trainingAll}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium"
          >
            <FiCpu /> {trainingAll ? 'Training All Models...' : 'Train All Models'}
          </button>
        </div>
        {trainAllError && (
          <p className="text-xs text-red-500 mb-3">{trainAllError}</p>
        )}
        {trainAllSummary && (
          <div className="mb-4 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
            Trained {trainAllSummary.trained} datasets. Target accuracy is {trainAllSummary.target_accuracy * 100}%. Results updated in the dataset cards.
          </div>
        )}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-gray-200">
              <tr>
                <th className="text-left py-2 px-3 font-semibold text-gray-900">Name</th>
                <th className="text-left py-2 px-3 font-semibold text-gray-900">Status</th>
                <th className="text-left py-2 px-3 font-semibold text-gray-900">Rows</th>
                <th className="text-left py-2 px-3 font-semibold text-gray-900">Quality</th>
                <th className="text-left py-2 px-3 font-semibold text-gray-900">Created</th>
                <th className="text-left py-2 px-3"></th>
              </tr>
            </thead>
            <tbody>
              {datasets.map((d) => (
                <React.Fragment key={d.id}>
                <tr className="border-b border-gray-100">
                  <td className="py-2 px-3 text-gray-900">
                    {d.name}
                    {d.id === activeDatasetId && (
                      <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">Active</span>
                    )}
                  </td>
                  <td className="py-2 px-3">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${statusBadge(d.status)}`}>
                      {d.status}
                    </span>
                    {d.status === 'failed' && d.error_message && (
                      <p className="text-xs text-red-500 mt-1 max-w-xs truncate" title={d.error_message}>{d.error_message}</p>
                    )}
                  </td>
                  <td className="py-2 px-3 text-gray-600">
                    {d.row_counts?.customers ? `${d.row_counts.customers.toLocaleString()} customers` : '—'}
                  </td>
                  <td className="py-2 px-3">
                    {d.quality_report ? (
                      <span className={`font-semibold ${completenessColor(d.quality_report.completeness_pct)}`}>
                        {d.quality_report.completeness_pct}%
                      </span>
                    ) : '—'}
                  </td>
                  <td className="py-2 px-3 text-gray-400">{new Date(d.created_at).toLocaleString()}</td>
                  <td className="py-2 px-3 flex gap-3 items-center">
                    {d.status === 'ready' && d.id !== activeDatasetId && (
                      <button onClick={() => handleActivate(d.id)} className="text-blue-500 hover:text-blue-700" title="Activate">
                        <FiPlay />
                      </button>
                    )}
                    {d.id !== 'default' && (
                      <button onClick={() => handleDelete(d.id)} className="text-red-500 hover:text-red-700" title="Delete">
                        <FiTrash2 />
                      </button>
                    )}
                    {d.status === 'ready' && (
                      <button onClick={() => toggleExpanded(d.id)} className="text-gray-500 hover:text-gray-700" title="Details">
                        {expandedId === d.id ? <FiChevronUp /> : <FiChevronDown />}
                      </button>
                    )}
                  </td>
                </tr>
                {expandedId === d.id && (
                  <tr className="bg-gray-50 border-b border-gray-100">
                    <td colSpan={6} className="py-4 px-3">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div>
                          <h4 className="text-sm font-semibold text-gray-800 mb-2 flex items-center gap-2">
                            <FiShield /> Data Quality Report
                          </h4>
                          {qualityError && (
                            <p className="text-xs text-red-500 mb-2">{qualityError}</p>
                          )}
                          {d.quality_report ? (
                            <>
                              <ul className="text-xs text-gray-600 space-y-1 mb-3">
                                <li>Total rows: <span className="font-medium">{d.quality_report.total_rows}</span></li>
                                <li>Duplicate customer IDs: <span className="font-medium">{d.quality_report.duplicate_customer_ids}</span></li>
                                <li>Missing emails: <span className="font-medium">{d.quality_report.missing_email}</span></li>
                                <li>Missing names: <span className="font-medium">{d.quality_report.missing_name}</span></li>
                                <li>Completeness: <span className={`font-medium ${completenessColor(d.quality_report.completeness_pct)}`}>{d.quality_report.completeness_pct}%</span></li>
                              </ul>
                              <button
                                onClick={() => handleRegenerateQualityReport(d.id)}
                                disabled={refreshingQualityId === d.id}
                                className="text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 px-3 py-1 rounded disabled:opacity-50"
                              >
                                {refreshingQualityId === d.id ? 'Refreshing...' : '🔄 Refresh Report'}
                              </button>
                            </>
                          ) : (
                            <p className="text-xs text-gray-400">No quality report available</p>
                          )}
                        </div>
                        <div>
                          <h4 className="text-sm font-semibold text-gray-800 mb-2 flex items-center gap-2">
                            <FiCpu /> Churn Prediction Model
                          </h4>
                          {trainError && (
                            <p className="text-xs text-red-500 mb-2">{trainError}</p>
                          )}
                          {d.model_metrics && !d.model_metrics.error ? (
                            <ul className="text-xs text-gray-600 space-y-1 mb-2">
                              <li>Accuracy: <span className="font-medium">{(d.model_metrics.accuracy * 100).toFixed(1)}%</span></li>
                              <li>Precision: <span className="font-medium">{(d.model_metrics.precision * 100).toFixed(1)}%</span></li>
                              <li>Recall: <span className="font-medium">{(d.model_metrics.recall * 100).toFixed(1)}%</span></li>
                              <li>F1 Score: <span className="font-medium">{(d.model_metrics.f1_score * 100).toFixed(1)}%</span></li>
                              <li>Trained on {d.model_metrics.training_samples} samples, tested on {d.model_metrics.test_samples}</li>
                              {d.model_metrics.feature_importances?.[0] && (
                                <li>Top predictor: <span className="font-medium">{d.model_metrics.feature_importances[0].feature}</span></li>
                              )}
                            </ul>
                          ) : (
                            <p className="text-xs text-gray-400 mb-2">No model trained yet</p>
                          )}
                          <button
                            onClick={() => handleTrainModel(d.id)}
                            disabled={trainingId === d.id}
                            className="flex items-center gap-2 px-3 py-1.5 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-lg text-xs font-medium"
                          >
                            <FiCpu /> {trainingId === d.id ? 'Training...' : 'Train Model'}
                          </button>
                        </div>
                        <div>
                          <h4 className="text-sm font-semibold text-gray-800 mb-2 flex items-center gap-2">
                            <FiAlertTriangle /> Anomaly Detection
                          </h4>
                          {detectError && (
                            <p className="text-xs text-red-500 mb-2">{detectError}</p>
                          )}
                          {d.anomaly_report && !d.anomaly_report.error ? (
                            <ul className="text-xs text-gray-600 space-y-1 mb-2">
                              <li>{d.anomaly_report.anomaly_count} of {d.anomaly_report.total_customers} customers flagged ({d.anomaly_report.anomaly_rate_pct}%)</li>
                              {d.anomaly_report.anomalies?.[0] && (
                                <li>Top anomaly: <span className="font-medium">{d.anomaly_report.anomalies[0].name}</span> (score {d.anomaly_report.anomalies[0].anomaly_score})</li>
                              )}
                            </ul>
                          ) : (
                            <p className="text-xs text-gray-400 mb-2">No anomaly scan run yet</p>
                          )}
                          <button
                            onClick={() => handleDetectAnomalies(d.id)}
                            disabled={detectingId === d.id}
                            className="flex items-center gap-2 px-3 py-1.5 bg-orange-600 hover:bg-orange-700 disabled:opacity-50 text-white rounded-lg text-xs font-medium"
                          >
                            <FiAlertTriangle /> {detectingId === d.id ? 'Scanning...' : 'Detect Anomalies'}
                          </button>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
                </React.Fragment>
              ))}
              {datasets.length === 0 && (
                <tr><td colSpan={6} className="text-center py-6 text-gray-400">No datasets yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default DatasetManager;
