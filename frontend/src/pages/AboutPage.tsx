import React from 'react';
import { 
  Info, 
  Layers, 
  ShieldCheck, 
  Cpu, 
  AlertTriangle, 
  Lock, 
  FileCheck, 
  GraduationCap,
  ExternalLink,
  Server
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const AboutPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-10 pb-16">
      {/* Title */}
      <div className="border-b border-slate-800 pb-6">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <Info className="w-8 h-8 text-cyan-400" />
          <span>About DBGuard</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Architectural principles, scientific threat model, memory bounds, and academic background.
        </p>
      </div>

      {/* Enterprise Specification Badge */}
      <div className="p-6 rounded-2xl border border-cyan-800/60 bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/40 space-y-3">
        <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold">
          <ShieldCheck className="w-5 h-5" />
          <span>Enterprise Database Reliability Specification</span>
        </div>
        <h2 className="text-xl font-bold text-white">
          DBGuard — Intelligent Integrity Assessment of Compressed Database Exports Without Full Database Restoration
        </h2>
        <p className="text-xs text-slate-300 leading-relaxed">
          Engineered for high-volume database environments where secondary scratch databases are financially or operationally prohibitive. DBGuard proves or disproves backup recoverability strictly in bounded <span className="font-mono text-cyan-300">O(B)</span> RAM.
        </p>
      </div>

      {/* The 3 Decoupled Tiers */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <Layers className="w-5 h-5 text-cyan-400" />
          The Three Verification Tiers
        </h3>
        <p className="text-xs text-slate-400 leading-relaxed">
          A fundamental contribution of DBGuard is separating physical decompression success from logical database integrity:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-2">
            <span className="font-mono text-xs font-semibold text-cyan-400 block">TIER 1</span>
            <h4 className="text-sm font-semibold text-white">Physical Stream Integrity</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Verifies container header signatures, magic bytes, DEFLATE/Brotli/XZ block framing, CRC32 trailer checksums, and premature EOF truncation.
            </p>
          </div>

          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-2">
            <span className="font-mono text-xs font-semibold text-cyan-400 block">TIER 2</span>
            <h4 className="text-sm font-semibold text-white">Structural / Syntactic Schema</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Validates record delimiters, UTF-8 byte sequences, unescaped quote invariants, column count consistency, and schema structural fingerprints.
            </p>
          </div>

          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-2">
            <span className="font-mono text-xs font-semibold text-cyan-400 block">TIER 3</span>
            <h4 className="text-sm font-semibold text-white">Provenance & Completeness</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Reconciles row counts and SHA-256 digests against independent trusted manifests generated synchronously at dump time by primary database triggers.
            </p>
          </div>
        </div>
      </div>

      {/* Solving the Core Paradox */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-3">
        <h3 className="text-base font-semibold text-white flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-amber-400" />
          Solving the Official Paradox (+30% Rows, -20% Compressed Size)
        </h3>
        <p className="text-xs text-slate-300 leading-relaxed">
          Traditional operations teams frequently panic when an export grows in row count by 30% but drops in compressed file size by 20%. DBGuard demonstrates that dictionary-based compression algorithms (DEFLATE / LZMA) scale inversely with Shannon information entropy:
        </p>
        <ul className="list-disc list-inside text-xs text-slate-400 space-y-1.5 pt-1">
          <li>High repetition in new records (e.g. repeated default foreign keys or status codes) drastically compresses.</li>
          <li>Shorter average string lengths reduce total decompressed byte volume.</li>
          <li>A high ratio of NULL columns collapses into minimal byte runs.</li>
        </ul>
        <p className="text-xs text-slate-300 pt-1">
          DBGuard tests the bitstream, proves zero byte truncation, and confirms that the export is structurally sound.
        </p>
      </div>

      {/* Technical Invariants & Security */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-3">
          <h4 className="text-sm font-semibold text-white flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            Bounded-Memory Invariant: O(B)
          </h4>
          <p className="text-xs text-slate-400 leading-relaxed">
            DBGuard processes multi-gigabyte files using a 64 KB sliding circular buffer. Memory consumption never exceeds 2 MB of resident RAM, completely eliminating Out-Of-Memory (OOM) crashes during emergency recovery drills.
          </p>
        </div>

        <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-3">
          <h4 className="text-sm font-semibold text-white flex items-center gap-2">
            <Lock className="w-4 h-4 text-cyan-400" />
            Security & Zip Bomb Immunity
          </h4>
          <p className="text-xs text-slate-400 leading-relaxed">
            DBGuard enforces strict decompression limits, aborting decompression if an archive exceeds maximum byte thresholds or exhibits recursive compression bombing traits (compression ratio &gt; 1000:1).
          </p>
        </div>
      </div>

      {/* Navigation CTA */}
      <div className="flex items-center justify-between p-6 rounded-2xl border border-cyan-800/40 bg-slate-900/80">
        <div>
          <h4 className="text-sm font-semibold text-white">Ready to Inspect Database Exports?</h4>
          <p className="text-xs text-slate-400">
            Launch a single-pass streaming audit, compare dual archives, or validate cryptographic manifests.
          </p>
        </div>
        <Link
          to="/analyze"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-semibold transition-all shadow-md shadow-cyan-500/20"
        >
          <span>Start Stream Analysis</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};

