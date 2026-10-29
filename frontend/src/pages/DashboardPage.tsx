import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  ShieldCheck, 
  Layers, 
  GitCompare, 
  AlertTriangle, 
  Play, 
  FileText, 
  Clock, 
  Trash2, 
  ExternalLink,
  Cpu,
  ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import { AnalysisSummary, DemoScenario } from '../types';
import StatusBadge from '../components/StatusBadge';
import MetricCard from '../components/MetricCard';

export const DashboardPage: React.FC = () => {
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [demos, setDemos] = useState<DemoScenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningDemoId, setRunningDemoId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [analysesData, demosData] = await Promise.all([
        api.listAnalyses().catch(() => []),
        api.getDemoScenarios().catch(() => []),
      ]);
      setAnalyses(analysesData);
      setDemos(demosData);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this analysis record?')) return;
    try {
      await api.deleteAnalysis(id);
      setAnalyses(analyses.filter((a) => a.id !== id));
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleRunDemo = async (scenarioId: string) => {
    try {
      setRunningDemoId(scenarioId);
      const result = await api.runDemoScenario(scenarioId);
      window.location.href = `/analysis/${result.summary.id}`;
    } catch (err: any) {
      alert(`Demo execution failed: ${err.message}`);
    } finally {
      setRunningDemoId(null);
    }
  };

  const totalRows = analyses.reduce((acc, curr) => acc + (curr.row_count || 0), 0);
  const totalPassed = analyses.filter((a) => a.analysis_status === 'PASS').length;
  const totalWarnings = analyses.filter((a) => a.analysis_status === 'WARNING').length;
  const totalFailures = analyses.filter((a) => a.analysis_status === 'FAIL').length;

  return (
    <div className="space-y-8 pb-12">
      {/* Header section */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            <span>Security & Integrity Dashboard</span>
            <span className="text-xs uppercase tracking-wider font-mono font-medium px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800/60">
              Live Engine
            </span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Real-time streaming telemetry, anomaly flags, and verification statuses for compressed database exports.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/analyze"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-sm transition-all shadow-md shadow-cyan-500/20"
          >
            <ShieldCheck className="w-4 h-4" />
            Analyze Export
          </Link>
          <Link
            to="/compare"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-medium text-sm transition-all border border-slate-700"
          >
            <GitCompare className="w-4 h-4" />
            Compare Dual
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/50 text-red-300 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Analyses Executed"
          value={analyses.length.toLocaleString()}
          icon={<Layers className="w-5 h-5" />}
          description="Bounded-memory single-pass audits"
        />
        <MetricCard
          label="Total Rows Streamed"
          value={totalRows.toLocaleString()}
          icon={<Cpu className="w-5 h-5" />}
          description="Decompressed in bounded RAM"
        />
        <MetricCard
          label="Verified Clean (Pass)"
          value={totalPassed}
          variant="success"
          icon={<ShieldCheck className="w-5 h-5" />}
          description="Passed all cryptographic & structural checks"
        />
        <MetricCard
          label="Anomalies / Failures"
          value={`${totalWarnings} Warn / ${totalFailures} Fail`}
          variant={totalFailures > 0 ? 'danger' : totalWarnings > 0 ? 'warning' : 'default'}
          icon={<AlertTriangle className="w-5 h-5" />}
          description="Integrity breaches or entropy anomalies"
        />
      </div>

      {/* Quick Launch Scenarios / Demo Suite */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <Play className="w-4 h-4 text-cyan-400" />
              Enterprise Diagnostic Scenarios
            </h2>
            <p className="text-xs text-slate-400">
              One-click reproducible datasets demonstrating the 30% row increase paradox, stream truncation, and manifest verification.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
          {demos.map((d) => (
            <div
              key={d.id}
              className="group relative flex flex-col justify-between p-4 rounded-xl border border-slate-800 bg-slate-950/70 hover:border-cyan-500/50 transition-all shadow-sm hover:shadow-cyan-500/10"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    {d.has_manifest ? 'Manifest Included' : 'No Manifest'}
                  </span>
                </div>
                <h3 className="text-sm font-semibold text-white group-hover:text-cyan-300 transition-colors">
                  {d.title}
                </h3>
                <p className="text-xs text-slate-400 mt-1.5 leading-relaxed line-clamp-3">
                  {d.description}
                </p>
              </div>

              <button
                onClick={() => handleRunDemo(d.id)}
                disabled={runningDemoId === d.id}
                className="mt-4 w-full flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg bg-cyan-950 hover:bg-cyan-900 border border-cyan-800/60 text-cyan-300 hover:text-white text-xs font-medium transition-all disabled:opacity-50"
              >
                {runningDemoId === d.id ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
                    <span>Streaming...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Run Scenario</span>
                  </>
                )}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Analyses Table */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur overflow-hidden">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Recent Integrity Analyses</h2>
            <p className="text-xs text-slate-400">
              Audit log of processed database archives, verification status, and calculated recovery scope.
            </p>
          </div>
          <button
            onClick={loadData}
            className="text-xs text-slate-400 hover:text-cyan-300 transition-colors px-3 py-1.5 rounded-lg border border-slate-800 hover:border-slate-700 bg-slate-950"
          >
            Refresh
          </button>
        </div>

        {loading ? (
          <div className="py-16 text-center text-slate-400 text-sm flex flex-col items-center justify-center gap-3">
            <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
            <span>Loading analysis history...</span>
          </div>
        ) : analyses.length === 0 ? (
          <div className="py-16 text-center text-slate-500 text-sm">
            No analyses recorded yet. Upload an export file or run a demo scenario above to begin.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-950/70 border-b border-slate-800 text-xs text-slate-400 uppercase font-mono tracking-wider">
                <tr>
                  <th className="py-3.5 px-4 font-semibold">Filename / ID</th>
                  <th className="py-3.5 px-4 font-semibold">Status</th>
                  <th className="py-3.5 px-4 font-semibold">Rows</th>
                  <th className="py-3.5 px-4 font-semibold">Compressed / Uncompressed</th>
                  <th className="py-3.5 px-4 font-semibold">Duration</th>
                  <th className="py-3.5 px-4 font-semibold">Recovery Assessment</th>
                  <th className="py-3.5 px-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {analyses.map((a) => (
                  <tr
                    key={a.id}
                    className="hover:bg-slate-800/40 transition-colors cursor-pointer group"
                    onClick={() => (window.location.href = `/analysis/${a.id}`)}
                  >
                    <td className="py-3.5 px-4 font-medium text-white">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-cyan-400" />
                        <div>
                          <span className="font-semibold text-slate-200 group-hover:text-cyan-300 transition-colors">
                            {a.original_filename}
                          </span>
                          <span className="block text-[11px] font-mono text-slate-500">
                            {a.id.slice(0, 8)}... &bull; {new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={a.analysis_status} />
                    </td>
                    <td className="py-3.5 px-4 font-mono text-xs text-slate-300">
                      {a.row_count?.toLocaleString() ?? 0}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-xs text-slate-400">
                      <span>{(a.compressed_size_bytes / 1024).toFixed(1)} KB</span>
                      <span className="text-slate-600 mx-1">/</span>
                      <span className="text-slate-300">{(a.decompressed_size_bytes / 1024).toFixed(1)} KB</span>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-xs text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-slate-500" />
                        <span>{a.execution_duration_sec.toFixed(3)}s</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800/80 text-cyan-300 border border-slate-700">
                        {a.recovery_assessment}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          to={`/analysis/${a.id}`}
                          onClick={(e) => e.stopPropagation()}
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                          title="View Details"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </Link>
                        <button
                          onClick={(e) => handleDelete(a.id, e)}
                          className="p-1.5 rounded-lg bg-red-950/40 hover:bg-red-900/60 text-red-400 hover:text-red-200 transition-colors"
                          title="Delete Analysis"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Core Database Recovery Clarification Card */}
      <div className="rounded-2xl border border-cyan-900/40 bg-gradient-to-r from-slate-900 via-slate-900/90 to-cyan-950/30 p-6">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-cyan-200">
              Why DBGuard Solves the Core Database Recovery Dilemma
            </h3>
            <p className="text-sm text-slate-400 max-w-3xl leading-relaxed">
              When production tables reach hundreds of gigabytes, DBAs lack time and scratch tablespaces to test-restore every compressed dump. 
              DBGuard uses single-pass streaming, DEFLATE/Brotli stream validation, row-level schema inspection, and Merkle tree hashing to certify recovery suitability in <span className="text-cyan-300 font-mono">O(B)</span> memory.
            </p>
          </div>
          <Link
            to="/about"
            className="flex-shrink-0 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-xs font-semibold uppercase tracking-wider transition-all"
          >
            <span>System Architecture</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
};

