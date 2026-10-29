import React, { useState } from 'react';
import { 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  HelpCircle, 
  Database, 
  Workflow, 
  Terminal,
  ArrowRight
} from 'lucide-react';
import { RecoveryClassification } from '../types';

interface ClassificationMeta {
  code: RecoveryClassification;
  title: string;
  badgeColor: string;
  description: string;
  verifiedScope: string;
  unverifiedScope: string;
  recommendedAction: string;
}

const CLASSIFICATIONS: ClassificationMeta[] = [
  {
    code: 'VERIFIED_WITHIN_SCOPE',
    title: 'Verified Within Scope',
    badgeColor: 'bg-emerald-950 text-emerald-400 border-emerald-800',
    description: 'The export bitstream is physically intact, checksums match, the format headers are valid, and an independently generated trusted manifest has confirmed record counts and hash digests.',
    verifiedScope: 'Physical container integrity, row count reconciliation, and logical schema consistency.',
    unverifiedScope: 'Source database state outside export window, uncommitted in-flight transactions.',
    recommendedAction: 'Safe to archive or use for primary production database restoration.',
  },
  {
    code: 'LIKELY_USABLE_BUT_NOT_FULLY_VERIFIED',
    title: 'Likely Usable, But Not Fully Verified',
    badgeColor: 'bg-cyan-950 text-cyan-400 border-cyan-800',
    description: 'The compressed archive decompress cleanly to the EOF sentinel, all rows parse according to schema, but no independent trusted manifest exists to mathematically prove that zero rows were dropped at source.',
    verifiedScope: 'Physical decompression stream validity and internal row syntax consistency.',
    unverifiedScope: 'Source table row count reconciliation (manifest absent).',
    recommendedAction: 'Proceed with restore in staging or compare against previous baseline exports before committing to prod.',
  },
  {
    code: 'RECOVERY_POSSIBLE_WITH_ERRORS',
    title: 'Recovery Possible With Errors / Salvageable',
    badgeColor: 'bg-amber-950 text-amber-400 border-amber-800',
    description: 'The export has suffered partial stream truncation or isolated corrupt records, but preceding blocks up to a determinable offset remain fully readable.',
    verifiedScope: 'Valid records up to failure offset.',
    unverifiedScope: 'Truncated tail blocks, discarded malformed records.',
    recommendedAction: 'Extract salvageable rows via streaming cut-off; do not drop existing tables before manual DBA review.',
  },
  {
    code: 'INTEGRITY_FAILURE',
    title: 'Integrity Breach / Unusable',
    badgeColor: 'bg-rose-950 text-rose-400 border-rose-800',
    description: 'Critical physical container checksum mismatch, premature stream termination, or massive schema corruption. Decompression aborted with fatal format errors.',
    verifiedScope: 'Definite physical or structural failure.',
    unverifiedScope: 'Corrupted payload contents.',
    recommendedAction: 'Reject dump immediately. Trigger emergency manual database re-export from source replica.',
  },
  {
    code: 'INCONCLUSIVE',
    title: 'Inconclusive Assessment',
    badgeColor: 'bg-slate-800 text-slate-300 border-slate-700',
    description: 'Ambiguous stream markers or statistical divergence (+30% rows / -20% size paradox) without sufficient baseline metadata to make a definitive pass/fail determination.',
    verifiedScope: 'Basic container readability.',
    unverifiedScope: 'Semantic record truth.',
    recommendedAction: 'Run comparative export diff against prior export cycle to evaluate entropy shift.',
  },
  {
    code: 'UNSUPPORTED_FORMAT',
    title: 'Unsupported Archive Format',
    badgeColor: 'bg-slate-900 text-slate-400 border-slate-800',
    description: 'Input container signature does not match supported streaming formats (Gzip, Bzip2, XZ, plain CSV, SQL dump).',
    verifiedScope: 'None.',
    unverifiedScope: 'All.',
    recommendedAction: 'Re-compress stream with standard gzip -c or use a supported container specification.',
  },
];

export const RecoveryPage: React.FC = () => {
  const [selectedClass, setSelectedClass] = useState<ClassificationMeta>(CLASSIFICATIONS[0]);

  return (
    <div className="space-y-8 pb-16">
      {/* Title */}
      <div className="border-b border-slate-800 pb-6">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <Workflow className="w-8 h-8 text-cyan-400" />
          <span>Recovery Assessment Framework</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          A formal, six-tier classification model mapping physical and logical verification evidence to concrete DBA disaster recovery decisions.
        </p>
      </div>

      {/* Interactive Classification Selector */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {CLASSIFICATIONS.map((c) => {
          const isSelected = selectedClass.code === c.code;
          return (
            <button
              key={c.code}
              onClick={() => setSelectedClass(c)}
              className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between ${
                isSelected
                  ? 'border-cyan-500 bg-cyan-950/20 shadow-md shadow-cyan-500/10'
                  : 'border-slate-800 bg-slate-900/40 hover:border-slate-700'
              }`}
            >
              <div>
                <span
                  className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-bold border mb-2 ${c.badgeColor}`}
                >
                  {c.code}
                </span>
                <h3 className="text-sm font-semibold text-white">{c.title}</h3>
              </div>
              <p className="text-xs text-slate-400 mt-2 line-clamp-2 leading-relaxed">
                {c.description}
              </p>
            </button>
          );
        })}
      </div>

      {/* Selected Classification Deep Dive */}
      <div className="p-6 rounded-2xl border border-cyan-800/60 bg-slate-900/70 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <span className="text-xs uppercase font-mono tracking-wider text-cyan-400 font-semibold block mb-1">
              Active Classification Spec
            </span>
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
              <span>{selectedClass.title}</span>
              <span
                className={`text-xs px-2.5 py-0.5 rounded-full font-mono border ${selectedClass.badgeColor}`}
              >
                {selectedClass.code}
              </span>
            </h2>
          </div>
        </div>

        <p className="text-sm text-slate-300 leading-relaxed">{selectedClass.description}</p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
            <span className="text-xs font-semibold text-emerald-400 uppercase font-mono flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Verified Scope
            </span>
            <p className="text-xs text-slate-300 leading-relaxed">{selectedClass.verifiedScope}</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
            <span className="text-xs font-semibold text-amber-400 uppercase font-mono flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5" />
              Unverified / Limitations
            </span>
            <p className="text-xs text-slate-300 leading-relaxed">{selectedClass.unverifiedScope}</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
            <span className="text-xs font-semibold text-cyan-400 uppercase font-mono flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5" />
              Recommended DBA Action
            </span>
            <p className="text-xs text-slate-300 leading-relaxed">{selectedClass.recommendedAction}</p>
          </div>
        </div>
      </div>

      {/* Decision Tree Guide */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 space-y-4">
        <h3 className="text-base font-semibold text-white flex items-center gap-2">
          <Database className="w-4 h-4 text-cyan-400" />
          The Scientific Decision Logic: Decompression vs Database Restoration Proof
        </h3>
        <p className="text-xs text-slate-400 leading-relaxed">
          In database disaster recovery engineering, decompressing a file successfully does <strong className="text-slate-200">not</strong> prove that the export represents a transactionally consistent snapshot of the source table. DBGuard enforces academic and industrial rigor through four sequential verification gates:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2">
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
            <span className="text-[11px] font-mono text-cyan-400 font-bold block">GATE 1: STREAM</span>
            <h4 className="text-xs font-semibold text-white">Physical Invariants</h4>
            <p className="text-[11px] text-slate-400">
              Check container headers, magic signatures, block bitstreams, and hardware CRC32/Adler32 checksums.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
            <span className="text-[11px] font-mono text-cyan-400 font-bold block">GATE 2: PARSER</span>
            <h4 className="text-xs font-semibold text-white">Syntax & Schema</h4>
            <p className="text-[11px] text-slate-400">
              Verify row delimiters, UTF-8 validity, unescaped quote invariants, and column count regularity.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
            <span className="text-[11px] font-mono text-cyan-400 font-bold block">GATE 3: STATS</span>
            <h4 className="text-xs font-semibold text-white">Entropy & Anomalies</h4>
            <p className="text-[11px] text-slate-400">
              Detect negative size divergence (+30% rows / -20% size), null ratios, and dictionary repetition shifts.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
            <span className="text-[11px] font-mono text-cyan-400 font-bold block">GATE 4: PROVENANCE</span>
            <h4 className="text-xs font-semibold text-white">Manifest Reconcile</h4>
            <p className="text-[11px] text-slate-400">
              Match independent source database manifests, cryptographic hashes, and HMAC signatures.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
