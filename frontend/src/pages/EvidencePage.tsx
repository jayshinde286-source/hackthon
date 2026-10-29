import React, { useEffect, useState } from 'react';
import { 
  ShieldCheck, 
  Filter, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  HelpCircle, 
  FileText,
  Search
} from 'lucide-react';
import { api } from '../api/client';
import { AnalysisSummary, IntegrityCheckItem, VerificationStatus } from '../types';
import StatusBadge from '../components/StatusBadge';

export const EvidencePage: React.FC = () => {
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string>('');
  const [checks, setChecks] = useState<IntegrityCheckItem[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true);
        const list = await api.listAnalyses();
        setAnalyses(list);
        if (list.length > 0) {
          setSelectedAnalysisId(list[0].id);
          const detail = await api.getAnalysisDetail(list[0].id);
          setChecks(detail.checks);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  const handleSelectAnalysis = async (id: string) => {
    setSelectedAnalysisId(id);
    try {
      setLoading(true);
      const detail = await api.getAnalysisDetail(id);
      setChecks(detail.checks);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filteredChecks = checks.filter((c) => {
    const matchesFilter = filterStatus === 'ALL' || c.status === filterStatus;
    const matchesSearch =
      c.check_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.explanation && c.explanation.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="space-y-8 pb-16">
      {/* Title */}
      <div className="border-b border-slate-800 pb-6">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <ShieldCheck className="w-8 h-8 text-cyan-400" />
          <span>Cryptographic & Structural Evidence</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Detailed audit trace of verifiable container invariants, header signatures, checksums, and manifest validations.
        </p>
      </div>

      {/* Select Analysis Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-2xl border border-slate-800 bg-slate-900/60">
        <div className="flex items-center gap-3 flex-1 max-w-md">
          <span className="text-xs uppercase font-mono tracking-wider font-semibold text-slate-300 flex-shrink-0">
            Source Export:
          </span>
          <select
            value={selectedAnalysisId}
            onChange={(e) => handleSelectAnalysis(e.target.value)}
            disabled={analyses.length === 0}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
          >
            {analyses.length === 0 ? (
              <option>No analysis records found</option>
            ) : (
              analyses.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.original_filename} ({a.row_count} rows, {a.analysis_status})
                </option>
              ))
            )}
          </select>
        </div>

        {/* Filter Buttons */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs text-slate-400 mr-1 flex items-center gap-1">
            <Filter className="w-3.5 h-3.5" />
            Filter:
          </span>
          {(['ALL', 'PASS', 'FAIL', 'WARNING', 'INCONCLUSIVE'] as const).map((status) => (
            <button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`px-3 py-1 rounded-lg text-xs font-mono font-semibold transition-all ${
                filterStatus === status
                  ? 'bg-cyan-500 text-slate-950 shadow-sm'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
        <input
          type="text"
          placeholder="Search checks, category, or evidence explanation..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full bg-slate-900/50 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500 transition-colors font-sans"
        />
      </div>

      {/* Evidence Table */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-slate-400 text-sm flex flex-col items-center justify-center gap-3">
            <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
            <span>Loading verification evidence checkpoints...</span>
          </div>
        ) : filteredChecks.length === 0 ? (
          <div className="py-16 text-center text-slate-500 text-sm">
            No verification checks match the selected criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase font-mono tracking-wider">
                <tr>
                  <th className="py-3 px-4 font-semibold">Scope / Category</th>
                  <th className="py-3 px-4 font-semibold">Invariant Check</th>
                  <th className="py-3 px-4 font-semibold">Evaluation Status</th>
                  <th className="py-3 px-4 font-semibold">Observed vs Expected</th>
                  <th className="py-3 px-4 font-semibold">Scientific Rationale</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {filteredChecks.map((check, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-medium text-cyan-400">
                      {check.category}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="font-semibold text-slate-200 block text-xs">
                        {check.check_name}
                      </span>
                      {check.evidence_reference && (
                        <span className="text-[11px] font-mono text-slate-500">
                          Ref: {check.evidence_reference}
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={check.status} />
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-300 text-[11px]">
                      <div>
                        <span className="text-slate-500">Observed: </span>
                        <span className="text-slate-200">{check.observed_value || 'None'}</span>
                      </div>
                      {check.expected_value && (
                        <div>
                          <span className="text-slate-500">Expected: </span>
                          <span className="text-emerald-400">{check.expected_value}</span>
                        </div>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 text-xs leading-relaxed max-w-sm">
                      {check.explanation || 'Verified invariant satisfied during stream pass.'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Scientific Citation Card */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-950 space-y-3 text-xs text-slate-400">
        <h4 className="font-semibold text-white flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-cyan-400" />
          The Three Tiers of Database Export Evidence
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
            <span className="font-semibold text-cyan-300 block">1. Physical Container Tier</span>
            <p className="text-[11px] text-slate-400">
              Verifies DEFLATE / Brotli / XZ bitstreams, container magic numbers, block boundaries, and hardware CRC32 checksums.
            </p>
          </div>
          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
            <span className="font-semibold text-cyan-300 block">2. Logical Structure Tier</span>
            <p className="text-[11px] text-slate-400">
              Validates record delimiters, UTF-8 byte encodings, column counts per row, and SQL syntax integrity without full database restoration.
            </p>
          </div>
          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
            <span className="font-semibold text-cyan-300 block">3. Provenance & Manifest Tier</span>
            <p className="text-[11px] text-slate-400">
              Reconciles independently generated manifests against the observed stream to establish completeness guarantees.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

