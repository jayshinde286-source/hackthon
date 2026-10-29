import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ShieldCheck, 
  AlertTriangle, 
  Clock, 
  Database, 
  FileDown, 
  Layers, 
  Hash, 
  CheckCircle2, 
  XCircle, 
  Info, 
  ArrowLeft,
  Server
} from 'lucide-react';
import { api } from '../api/client';
import { AnalysisDetail } from '../types';
import StatusBadge from '../components/StatusBadge';
import MetricCard from '../components/MetricCard';

export const AnalysisResultPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [detail, setDetail] = useState<AnalysisDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'evidence' | 'compression' | 'anomalies' | 'schema'>('evidence');

  useEffect(() => {
    if (!id) return;
    const fetchDetail = async () => {
      try {
        setLoading(true);
        const data = await api.getAnalysisDetail(id);
        setDetail(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load analysis result');
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [id]);

  if (loading) {
    return (
      <div className="py-24 text-center text-slate-400 text-sm flex flex-col items-center justify-center gap-3">
        <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
        <span>Loading verification telemetry...</span>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center space-y-4">
        <div className="inline-flex p-3 rounded-2xl bg-red-950/50 border border-red-800 text-red-400">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-white">Analysis Not Found</h2>
        <p className="text-sm text-slate-400">{error || 'Unable to retrieve analysis details.'}</p>
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 text-white text-xs font-semibold hover:bg-slate-700 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const { summary, checks, anomalies, recovery, full_report } = detail;
  const compressionRatio =
    summary.compressed_size_bytes > 0
      ? (summary.decompressed_size_bytes / summary.compressed_size_bytes).toFixed(2)
      : '0.00';

  return (
    <div className="space-y-8 pb-16">
      {/* Navigation & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-cyan-400 mb-2 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Dashboard</span>
          </Link>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            <span>{summary.original_filename}</span>
            <StatusBadge status={summary.analysis_status} />
          </h1>
          <div className="flex items-center gap-4 text-xs font-mono text-slate-400 mt-2">
            <span>ID: {summary.id}</span>
            <span>&bull;</span>
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              {summary.execution_duration_sec.toFixed(3)}s execution
            </span>
            <span>&bull;</span>
            <span>{new Date(summary.created_at).toLocaleString()}</span>
          </div>
        </div>

        {/* Download Reports Button Group */}
        <div className="flex items-center gap-2 flex-wrap">
          <a
            href={api.getReportDownloadUrl(summary.id, 'pdf')}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
          >
            <FileDown className="w-4 h-4 text-rose-400" />
            PDF Report
          </a>
          <a
            href={api.getReportDownloadUrl(summary.id, 'json')}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
          >
            <FileDown className="w-4 h-4 text-amber-400" />
            JSON Manifest
          </a>
          <a
            href={api.getReportDownloadUrl(summary.id, 'csv')}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
          >
            <FileDown className="w-4 h-4 text-emerald-400" />
            CSV Summary
          </a>
        </div>
      </div>

      {/* Recovery Executive Verdict Banner */}
      <div className="p-6 rounded-2xl border border-cyan-800/50 bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/40 relative overflow-hidden">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase font-mono tracking-wider font-semibold text-cyan-400">
                Executive Recovery Assessment
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-700">
                {recovery.classification}
              </span>
            </div>
            <p className="text-base font-medium text-slate-200">{recovery.summary}</p>
            <p className="text-xs text-slate-400">
              Recoverable Record Estimate:{' '}
              <span className="text-cyan-300 font-mono font-semibold">
                {recovery.recoverable_record_estimate.toLocaleString()} rows
              </span>
            </p>
          </div>
          <Link
            to="/recovery"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition-colors flex-shrink-0"
          >
            <span>Recovery Classification Framework</span>
            <Info className="w-3.5 h-3.5 text-cyan-400" />
          </Link>
        </div>
      </div>

      {/* Metric Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Streamed Rows"
          value={summary.row_count.toLocaleString()}
          icon={<Database className="w-5 h-5" />}
          description="Bounded-stream count"
        />
        <MetricCard
          label="Compressed Archive Size"
          value={`${(summary.compressed_size_bytes / 1024).toFixed(1)} KB`}
          icon={<Layers className="w-5 h-5" />}
          description={`${summary.compression_format.toUpperCase()} Container`}
        />
        <MetricCard
          label="Decompressed Volume"
          value={`${(summary.decompressed_size_bytes / 1024).toFixed(1)} KB`}
          icon={<Server className="w-5 h-5" />}
          description={`Decompression ratio: ${compressionRatio}x`}
        />
        <MetricCard
          label="Stream Integrity Status"
          value={summary.analysis_status}
          variant={
            summary.analysis_status === 'PASS'
              ? 'success'
              : summary.analysis_status === 'FAIL'
              ? 'danger'
              : 'warning'
          }
          icon={<ShieldCheck className="w-5 h-5" />}
          description={`${checks.filter((c) => c.status === 'PASS').length} of ${checks.length} checks passed`}
        />
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-800 flex items-center gap-2">
        <button
          onClick={() => setActiveTab('evidence')}
          className={`px-4 py-2.5 text-sm font-semibold transition-all border-b-2 flex items-center gap-2 ${
            activeTab === 'evidence'
              ? 'border-cyan-400 text-cyan-400 bg-cyan-950/20'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>Verification Evidence Matrix ({checks.length})</span>
        </button>
        <button
          onClick={() => setActiveTab('compression')}
          className={`px-4 py-2.5 text-sm font-semibold transition-all border-b-2 flex items-center gap-2 ${
            activeTab === 'compression'
              ? 'border-cyan-400 text-cyan-400 bg-cyan-950/20'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Hash className="w-4 h-4" />
          <span>Stream & Hashes</span>
        </button>
        <button
          onClick={() => setActiveTab('anomalies')}
          className={`px-4 py-2.5 text-sm font-semibold transition-all border-b-2 flex items-center gap-2 ${
            activeTab === 'anomalies'
              ? 'border-cyan-400 text-cyan-400 bg-cyan-950/20'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <AlertTriangle className="w-4 h-4" />
          <span>Anomalies Flagged ({anomalies.length})</span>
        </button>
        <button
          onClick={() => setActiveTab('schema')}
          className={`px-4 py-2.5 text-sm font-semibold transition-all border-b-2 flex items-center gap-2 ${
            activeTab === 'schema'
              ? 'border-cyan-400 text-cyan-400 bg-cyan-950/20'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Database className="w-4 h-4" />
          <span>Table Schema & Columns</span>
        </button>
      </div>

      {/* Tab 1: Verification Evidence Matrix */}
      {activeTab === 'evidence' && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <span className="text-xs uppercase font-mono tracking-wider text-slate-400 font-semibold">
              Granular Verification Checkpoints
            </span>
            <span className="text-xs text-slate-500 font-mono">
              Evaluated in O(B) memory during stream
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-950/70 border-b border-slate-800 text-xs text-slate-400 uppercase font-mono">
                <tr>
                  <th className="py-3 px-4 font-semibold">Category</th>
                  <th className="py-3 px-4 font-semibold">Verification Check</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold">Observed / Expected</th>
                  <th className="py-3 px-4 font-semibold">Evidence Reference</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {checks.map((c, i) => (
                  <tr key={i} className="hover:bg-slate-800/30">
                    <td className="py-3 px-4 font-mono text-xs text-slate-400">{c.category}</td>
                    <td className="py-3 px-4 font-medium text-slate-200">
                      <div>
                        <span>{c.check_name}</span>
                        {c.explanation && (
                          <span className="block text-xs text-slate-400 font-normal mt-0.5">
                            {c.explanation}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={c.status} />
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-slate-300">
                      <div>
                        <span className="text-slate-400">Observed: </span>
                        <span>{c.observed_value || 'N/A'}</span>
                      </div>
                      {c.expected_value && (
                        <div>
                          <span className="text-slate-400">Expected: </span>
                          <span className="text-emerald-400">{c.expected_value}</span>
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-500">
                      {c.evidence_reference || 'Self-contained stream assertion'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Stream & Hashes */}
      {activeTab === 'compression' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 space-y-4">
            <h3 className="text-sm font-semibold text-white uppercase font-mono tracking-wider">
              Cryptographic Hash Digests
            </h3>
            <div className="space-y-4">
              <div>
                <span className="text-xs text-slate-400 block mb-1">
                  Compressed Stream SHA-256 (Physical)
                </span>
                <code className="block p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-cyan-300 break-all select-all">
                  {summary.compressed_sha256}
                </code>
              </div>
              {summary.decompressed_sha256 && (
                <div>
                  <span className="text-xs text-slate-400 block mb-1">
                    Decompressed Content SHA-256 (Logical)
                  </span>
                  <code className="block p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-emerald-300 break-all select-all">
                    {summary.decompressed_sha256}
                  </code>
                </div>
              )}
              {summary.schema_fingerprint && (
                <div>
                  <span className="text-xs text-slate-400 block mb-1">
                    Schema Structural Fingerprint
                  </span>
                  <code className="block p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-amber-300 break-all select-all">
                    {summary.schema_fingerprint}
                  </code>
                </div>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 space-y-4">
            <h3 className="text-sm font-semibold text-white uppercase font-mono tracking-wider">
              Stream Telemetry & Metrics
            </h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between py-2 border-b border-slate-800">
                <span className="text-slate-400">Compression Format</span>
                <span className="font-mono text-white uppercase">{summary.compression_format}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-800">
                <span className="text-slate-400">Data Format</span>
                <span className="font-mono text-white uppercase">{summary.data_format}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-800">
                <span className="text-slate-400">Compressed Bytes</span>
                <span className="font-mono text-white">
                  {summary.compressed_size_bytes.toLocaleString()} bytes
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-800">
                <span className="text-slate-400">Decompressed Bytes</span>
                <span className="font-mono text-white">
                  {summary.decompressed_size_bytes.toLocaleString()} bytes
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-800">
                <span className="text-slate-400">Compression Efficiency</span>
                <span className="font-mono text-cyan-300 font-semibold">{compressionRatio}x</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-slate-400">Avg Bytes / Row</span>
                <span className="font-mono text-white">
                  {summary.row_count > 0
                    ? (summary.decompressed_size_bytes / summary.row_count).toFixed(1)
                    : 0}{' '}
                  bytes
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Anomalies Flagged */}
      {activeTab === 'anomalies' && (
        <div className="space-y-4">
          {anomalies.length === 0 ? (
            <div className="rounded-2xl border border-emerald-900/40 bg-emerald-950/20 p-8 text-center space-y-2">
              <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
              <h4 className="text-base font-semibold text-emerald-200">
                No Integrity Anomalies Detected
              </h4>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                No physical stream truncation, column count mismatch, or statistical paradoxes were discovered in this export.
              </p>
            </div>
          ) : (
            anomalies.map((a, i) => (
              <div
                key={i}
                className="p-5 rounded-2xl border border-amber-900/50 bg-amber-950/20 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    <span className="font-mono text-xs font-semibold text-amber-300">
                      Rule: {a.rule_id}
                    </span>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-amber-900/60 text-amber-200">
                    {a.severity}
                  </span>
                </div>
                <p className="text-sm font-medium text-slate-200">{a.explanation}</p>
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-300">
                  <span className="font-semibold text-cyan-400">DBA Recommendation: </span>
                  {a.recommendation}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Tab 4: Schema & Columns */}
      {activeTab === 'schema' && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white uppercase font-mono tracking-wider">
              Discovered Table Schema ({summary.column_count} Columns)
            </h3>
            <span className="text-xs text-slate-400 font-mono">
              Fingerprint: {summary.schema_fingerprint?.slice(0, 16)}...
            </span>
          </div>

          {full_report?.schema?.columns ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-950/70 border-b border-slate-800 text-xs text-slate-400 uppercase font-mono">
                  <tr>
                    <th className="py-2.5 px-3">Column Index</th>
                    <th className="py-2.5 px-3">Column Name</th>
                    <th className="py-2.5 px-3">Inferred Type</th>
                    <th className="py-2.5 px-3">Nullability</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 font-sans">
                  {full_report.schema.columns.map((col: any, idx: number) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 font-mono text-xs text-slate-500">#{idx + 1}</td>
                      <td className="py-2.5 px-3 font-mono text-xs font-semibold text-slate-200">
                        {col.name || `col_${idx + 1}`}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-xs text-cyan-300">
                        {col.data_type || 'TEXT'}
                      </td>
                      <td className="py-2.5 px-3 text-xs text-slate-400">
                        {col.nullable ? 'NULLABLE' : 'NOT NULL'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400">
              Columns inferred directly from header row: {summary.column_count} fields detected.
            </div>
          )}
        </div>
      )}
    </div>
  );
};

