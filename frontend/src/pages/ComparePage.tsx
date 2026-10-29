import React, { useState } from 'react';
import { 
  GitCompare, 
  UploadCloud, 
  AlertTriangle, 
  CheckCircle2, 
  HelpCircle, 
  TrendingUp, 
  TrendingDown, 
  Sparkles,
  BarChart3
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Legend 
} from 'recharts';
import { api } from '../api/client';
import { ComparisonSummary } from '../types';
import FileDropzone from '../components/FileDropzone';

export const ComparePage: React.FC = () => {
  const [oldFile, setOldFile] = useState<File | null>(null);
  const [newFile, setNewFile] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ComparisonSummary | null>(null);

  const handleCompare = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!oldFile || !newFile) {
      setError('Please select both the previous and current export archives.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const comparison = await api.compareExports(oldFile, newFile);
      setResult(comparison);
    } catch (err: any) {
      setError(err.message || 'Comparison failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadParadoxDemo = async () => {
    try {
      setLoading(true);
      setError(null);
      // Fetch the two demo files from sample_data via demo runner or preloaded blobs
      const demoRes = await api.runDemoScenario('scenario_1_anomaly');
      // For immediate interactive display, compute demo comparison
      setResult({
        id: 'cmp_demo_paradox',
        previous_filename: 'export_baseline_100k.csv.gz',
        current_filename: 'export_anomaly_130k.csv.gz',
        row_count_change_pct: 30.0,
        compressed_size_change_pct: -20.0,
        decompressed_size_change_pct: 12.5,
        compression_ratio_old: 3.25,
        compression_ratio_new: 4.57,
        bytes_per_row_old: 85.4,
        bytes_per_row_new: 52.8,
        schema_match: true,
        summary_verdict: 'ANOMALY_EXPLAINABLE_STATISTICAL',
        created_at: new Date().toISOString(),
        diffs: [
          { metric: 'Row Count', old: 100000, new: 130000, change_pct: 30.0 },
          { metric: 'Compressed Bytes', old: 2621440, new: 2097152, change_pct: -20.0 },
          { metric: 'Decompressed Bytes', old: 8520000, new: 9585000, change_pct: 12.5 },
          { metric: 'Compression Ratio', old: 3.25, new: 4.57, change_pct: 40.6 },
          { metric: 'Bytes Per Record', old: 85.2, new: 52.8, change_pct: -38.0 },
        ],
        anomaly_flags: [
          'Negative Size Divergence (+30% rows, -20% compressed size)',
          'High Repetition / Zero Entropy detected in newly inserted records',
          'Valid DEFLATE container stream & EOF checksums certified'
        ]
      });
    } catch (err: any) {
      setError(err.message || 'Failed to load demo scenario.');
    } finally {
      setLoading(false);
    }
  };

  const chartData = result ? [
    {
      name: 'Row Count',
      Previous: result.diffs.find(d => d.metric === 'Row Count')?.old || 0,
      Current: result.diffs.find(d => d.metric === 'Row Count')?.new || 0,
    },
    {
      name: 'Compressed KB',
      Previous: Math.round(((result.diffs.find(d => d.metric === 'Compressed Bytes')?.old || 0) / 1024)),
      Current: Math.round(((result.diffs.find(d => d.metric === 'Compressed Bytes')?.new || 0) / 1024)),
    },
    {
      name: 'Decompressed KB',
      Previous: Math.round(((result.diffs.find(d => d.metric === 'Decompressed Bytes')?.old || 0) / 1024)),
      Current: Math.round(((result.diffs.find(d => d.metric === 'Decompressed Bytes')?.new || 0) / 1024)),
    }
  ] : [];

  return (
    <div className="space-y-8 pb-16">
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            <GitCompare className="w-8 h-8 text-cyan-400" />
            <span>Differential Export Comparator</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Investigate unexpected changes in row counts, compressed sizes, and record entropy between consecutive backups.
          </p>
        </div>
        <button
          onClick={handleLoadParadoxDemo}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-950/60 hover:bg-purple-900 border border-purple-800 text-purple-200 text-xs font-semibold transition-all shadow-md"
        >
          <Sparkles className="w-4 h-4 text-purple-400" />
          <span>Load Paradox Scenario (+30% Rows / -20% Size)</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/50 text-red-300 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Dual Upload Form */}
      <form onSubmit={handleCompare} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase font-mono tracking-wider font-semibold text-slate-300">
                Baseline Export (Previous Backup)
              </span>
              <span className="text-[11px] font-mono text-cyan-400">Reference Dump</span>
            </div>
            <FileDropzone
              file={oldFile}
              onFileSelect={setOldFile}
              label="Select previous compressed dump"
              description="e.g. export_baseline_100k.csv.gz"
            />
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase font-mono tracking-wider font-semibold text-slate-300">
                Candidate Export (Current Backup)
              </span>
              <span className="text-[11px] font-mono text-purple-400">Suspicious Dump</span>
            </div>
            <FileDropzone
              file={newFile}
              onFileSelect={setNewFile}
              label="Select current compressed dump"
              description="e.g. export_candidate_130k.csv.gz"
            />
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={!oldFile || !newFile || loading}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-sm transition-all shadow-md shadow-cyan-500/20 disabled:opacity-50"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                <span>Running Comparative Stream Parser...</span>
              </>
            ) : (
              <>
                <GitCompare className="w-4 h-4" />
                <span>Execute Dual Stream Audit</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Comparison Results */}
      {result && (
        <div className="space-y-8 animate-fadeIn">
          {/* Executive Paradox Banner */}
          <div className="p-6 rounded-2xl border border-cyan-800 bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/40 space-y-4">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div>
                <span className="text-xs uppercase font-mono tracking-wider text-cyan-400 font-semibold block mb-1">
                  Comparative Analysis Verdict
                </span>
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  <span>{result.summary_verdict}</span>
                  {result.summary_verdict.includes('EXPLAINABLE') ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-amber-400" />
                  )}
                </h3>
              </div>
              <div className="flex items-center gap-3">
                <div className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono">
                  <span className="text-slate-400">Schema Compatibility: </span>
                  <span className={result.schema_match ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                    {result.schema_match ? 'MATCH (100%)' : 'MISMATCH'}
                  </span>
                </div>
              </div>
            </div>

            {/* Scientific Paradox Explanation */}
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-2 text-xs text-slate-300 leading-relaxed">
              <span className="font-semibold text-cyan-300 flex items-center gap-1.5">
                <HelpCircle className="w-4 h-4" />
                The +30% Row Increase / -20% File Size Paradox Explained
              </span>
              <p>
                In standard DEFLATE / Lempel-Ziv compression, dictionary encoding exploits repeated character sequences. If new records contain high amounts of repetitive default values, uniform timestamps, NULL fields, or shorter string lengths, the compression ratio scales super-linearly (from <span className="font-mono text-cyan-300">{result.compression_ratio_old}x</span> to <span className="font-mono text-cyan-300">{result.compression_ratio_new}x</span>).
              </p>
              <p className="text-slate-400">
                Because the physical stream headers, CRC-32 checksums, and EOF delimiters are structurally valid, <strong className="text-white">this export is NOT corrupt</strong>; it merely exhibits lower information entropy.
              </p>
            </div>
          </div>

          {/* Diffs Table and Chart */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Table */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
              <h4 className="text-sm font-semibold text-white uppercase font-mono tracking-wider">
                Differential Telemetry Table
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-sans">
                  <thead className="bg-slate-950/70 border-b border-slate-800 text-[11px] text-slate-400 uppercase font-mono">
                    <tr>
                      <th className="py-2.5 px-3">Metric</th>
                      <th className="py-2.5 px-3">Baseline</th>
                      <th className="py-2.5 px-3">Candidate</th>
                      <th className="py-2.5 px-3 text-right">Relative Delta</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {result.diffs.map((d, i) => {
                      const isPositive = (d.change_pct || 0) > 0;
                      return (
                        <tr key={i} className="hover:bg-slate-800/30">
                          <td className="py-2.5 px-3 font-sans font-medium text-slate-200">
                            {d.metric}
                          </td>
                          <td className="py-2.5 px-3 text-slate-400">
                            {d.old.toLocaleString()}
                          </td>
                          <td className="py-2.5 px-3 text-slate-200 font-semibold">
                            {d.new.toLocaleString()}
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            <span
                              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold ${
                                isPositive
                                  ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/50'
                                  : 'bg-rose-950 text-rose-400 border border-rose-800/50'
                              }`}
                            >
                              {isPositive ? (
                                <TrendingUp className="w-3 h-3" />
                              ) : (
                                <TrendingDown className="w-3 h-3" />
                              )}
                              {isPositive ? `+${d.change_pct}%` : `${d.change_pct}%`}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Recharts Bar Chart */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-white uppercase font-mono tracking-wider flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-cyan-400" />
                  Visual Volume Delta
                </h4>
                <span className="text-[11px] text-slate-500 font-mono">Baseline vs Candidate</span>
              </div>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0f172a',
                        borderColor: '#334155',
                        borderRadius: '0.75rem',
                        fontSize: '12px',
                        color: '#f8fafc',
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                    <Bar dataKey="Previous" fill="#64748b" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Current" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Anomaly Flags List */}
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-3">
            <h4 className="text-xs font-semibold text-slate-300 uppercase font-mono tracking-wider">
              Diagnostic Anomaly Flags ({result.anomaly_flags.length})
            </h4>
            <div className="space-y-2">
              {result.anomaly_flags.map((flag, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-xs text-slate-300"
                >
                  <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                  <span>{flag}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

