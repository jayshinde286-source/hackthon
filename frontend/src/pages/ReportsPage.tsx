import React, { useEffect, useState } from 'react';
import { 
  FileText, 
  FileDown, 
  Clock, 
  CheckCircle2, 
  AlertTriangle, 
  Eye, 
  ShieldCheck,
  Search
} from 'lucide-react';
import { api } from '../api/client';
import { AnalysisSummary } from '../types';
import StatusBadge from '../components/StatusBadge';

export const ReportsPage: React.FC = () => {
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAnalysis, setSelectedAnalysis] = useState<AnalysisSummary | null>(null);

  useEffect(() => {
    const fetchAnalyses = async () => {
      try {
        setLoading(true);
        const data = await api.listAnalyses();
        setAnalyses(data);
        if (data.length > 0) {
          setSelectedAnalysis(data[0]);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalyses();
  }, []);

  const filteredAnalyses = analyses.filter((a) =>
    a.original_filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-8 pb-16">
      {/* Title */}
      <div className="border-b border-slate-800 pb-6">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <FileText className="w-8 h-8 text-cyan-400" />
          <span>Audit Reports & Export Center</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Download executive-grade PDF reports, JSON cryptographic audit manifests, and tabular CSV summaries.
        </p>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
        <input
          type="text"
          placeholder="Search by filename or analysis ID..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full bg-slate-900/60 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500 transition-colors"
        />
      </div>

      {/* Main Grid: List on Left, Preview on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Reports Table (2 cols) */}
        <div className="lg:col-span-2 rounded-2xl border border-slate-800 bg-slate-900/40 overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <span className="text-xs uppercase font-mono tracking-wider font-semibold text-slate-400">
              Generated Audit Reports ({filteredAnalyses.length})
            </span>
          </div>

          {loading ? (
            <div className="py-16 text-center text-slate-400 text-sm flex flex-col items-center justify-center gap-3">
              <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
              <span>Loading reports...</span>
            </div>
          ) : filteredAnalyses.length === 0 ? (
            <div className="py-16 text-center text-slate-500 text-sm">
              No analysis records found.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-sans">
                <thead className="bg-slate-950/70 border-b border-slate-800 text-[11px] text-slate-400 uppercase font-mono">
                  <tr>
                    <th className="py-3 px-4">Export File</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Rows</th>
                    <th className="py-3 px-4 text-right">Download Formats</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-sans">
                  {filteredAnalyses.map((a) => {
                    const isSelected = selectedAnalysis?.id === a.id;
                    return (
                      <tr
                        key={a.id}
                        onClick={() => setSelectedAnalysis(a)}
                        className={`cursor-pointer transition-colors ${
                          isSelected ? 'bg-cyan-950/30' : 'hover:bg-slate-800/30'
                        }`}
                      >
                        <td className="py-3.5 px-4 font-medium text-slate-200">
                          <div>
                            <span className="font-semibold block text-white">
                              {a.original_filename}
                            </span>
                            <span className="text-[11px] font-mono text-slate-500">
                              {new Date(a.created_at).toLocaleDateString()} &bull; ID: {a.id.slice(0, 8)}...
                            </span>
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          <StatusBadge status={a.analysis_status} />
                        </td>
                        <td className="py-3.5 px-4 font-mono text-slate-300">
                          {a.row_count.toLocaleString()}
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <div
                            className="flex items-center justify-end gap-1.5"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <a
                              href={api.getReportDownloadUrl(a.id, 'pdf')}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-rose-300 text-[11px] font-semibold border border-slate-700 transition-colors"
                              title="Download PDF Report"
                            >
                              PDF
                            </a>
                            <a
                              href={api.getReportDownloadUrl(a.id, 'json')}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-amber-300 text-[11px] font-semibold border border-slate-700 transition-colors"
                              title="Download JSON Manifest"
                            >
                              JSON
                            </a>
                            <a
                              href={api.getReportDownloadUrl(a.id, 'csv')}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-emerald-300 text-[11px] font-semibold border border-slate-700 transition-colors"
                              title="Download CSV Summary"
                            >
                              CSV
                            </a>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Live Report Preview (1 col) */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <span className="text-xs uppercase font-mono tracking-wider font-semibold text-cyan-400 flex items-center gap-1.5">
              <Eye className="w-4 h-4" />
              Report Summary Preview
            </span>
          </div>

          {selectedAnalysis ? (
            <div className="space-y-4 text-xs font-mono">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="text-white font-semibold font-sans text-sm">
                  {selectedAnalysis.original_filename}
                </div>
                <div className="text-slate-400 text-[11px]">
                  Analysis ID: <span className="text-cyan-300">{selectedAnalysis.id}</span>
                </div>
                <div className="text-slate-400 text-[11px]">
                  Assessment:{' '}
                  <span className="text-emerald-400 font-bold">
                    {selectedAnalysis.recovery_assessment}
                  </span>
                </div>
              </div>

              <div className="space-y-2 text-slate-300">
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-500">Record Count:</span>
                  <span className="text-white">{selectedAnalysis.row_count.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-500">Compressed:</span>
                  <span className="text-white">
                    {(selectedAnalysis.compressed_size_bytes / 1024).toFixed(1)} KB
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-500">Decompressed:</span>
                  <span className="text-white">
                    {(selectedAnalysis.decompressed_size_bytes / 1024).toFixed(1)} KB
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-500">Execution Duration:</span>
                  <span className="text-white">
                    {selectedAnalysis.execution_duration_sec.toFixed(3)}s
                  </span>
                </div>
              </div>

              <div className="pt-2">
                <span className="text-slate-500 block mb-1">Physical SHA-256 Digest:</span>
                <code className="block p-2 rounded-lg bg-slate-950 border border-slate-800 text-[10px] text-cyan-400 break-all select-all">
                  {selectedAnalysis.compressed_sha256}
                </code>
              </div>

              <div className="pt-3 flex flex-col gap-2">
                <a
                  href={api.getReportDownloadUrl(selectedAnalysis.id, 'pdf')}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full flex items-center justify-center gap-2 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-sans text-xs font-semibold border border-slate-700 transition-colors"
                >
                  <FileDown className="w-4 h-4 text-rose-400" />
                  Download PDF Report
                </a>
              </div>
            </div>
          ) : (
            <div className="py-12 text-center text-slate-500 text-xs">
              Select an analysis on the left to preview its report metadata.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

