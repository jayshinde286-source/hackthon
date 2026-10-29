import React from 'react';
import { Link } from 'react-router-dom';
import {
  Zap,
  ArrowRight,
  AlertTriangle,
  GitCompare,
  GraduationCap,
  Sparkles,
  Lock,
  Layers,
  Activity
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="space-y-16 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-cyan-950 p-8 md:p-14 text-white shadow-xl border border-slate-800">
        <div className="absolute top-0 right-0 -mr-20 -mt-20 h-96 w-96 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 -mb-20 h-80 w-80 rounded-full bg-blue-500/10 blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full bg-cyan-950/80 px-3.5 py-1 text-xs font-mono font-medium text-cyan-300 border border-cyan-800">
            <Sparkles className="h-3.5 w-3.5" />
            <span>CSE Mini-Project &bull; Autonomous Verification Engine</span>
          </div>

          <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight">
            DBGuard: Intelligent Integrity Assessment of Compressed Database Exports
          </h1>

          <p className="text-base md:text-lg text-slate-300 font-normal leading-relaxed">
            Verify the physical decodability, cryptographic consistency, and recovery readiness of massive compressed database archives <strong className="text-white">without secondary database restoration</strong>.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 rounded-xl bg-cyan-500 px-6 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-500/20 transition-all hover:bg-cyan-400 active:scale-95"
            >
              <span>Launch Dashboard</span>
              <ArrowRight className="h-4 w-4" />
            </Link>

            <Link
              to="/compare"
              className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800/80 px-5 py-3 text-sm font-semibold text-slate-200 transition-all hover:bg-slate-700 active:scale-95"
            >
              <GitCompare className="h-4 w-4 text-cyan-400" />
              <span>Investigate Paradox (+30% / -20%)</span>
            </Link>

            <Link
              to="/viva-guide"
              className="inline-flex items-center gap-2 rounded-xl border border-purple-800/60 bg-purple-950/40 px-5 py-3 text-sm font-semibold text-purple-300 transition-all hover:bg-purple-900/60 active:scale-95"
            >
              <GraduationCap className="h-4 w-4" />
              <span>Viva Guide (25 Q&A)</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Official Mini-Project Problem Statement Highlight */}
      <section className="rounded-2xl border border-cyan-900/60 bg-slate-900/50 p-8 space-y-4">
        <div className="flex items-center gap-2 text-cyan-400">
          <AlertTriangle className="h-5 w-5" />
          <h2 className="text-xs font-mono font-bold uppercase tracking-wider">
            Official University Problem Statement
          </h2>
        </div>

        <blockquote className="rounded-xl border-l-4 border-cyan-500 bg-slate-950/80 p-5 text-sm md:text-base italic text-slate-200 leading-relaxed font-serif">
          "It is observed that export file-size usually grows when the number of rows exported increases. However, once it was observed that number of rows increased by 30% as compared to an earlier export, but file size was reduced by 20%. Management was suspicious of the usability of the export file from a data recovery point of view. Since the table is very large, there is no time scope and tablespace scope to re-import it into another temporary database to validate if all data is intact."
        </blockquote>

        <p className="text-xs text-slate-400 leading-relaxed">
          DBGuard resolves this dilemma by streaming compressed blocks through an <strong className="text-slate-200 font-mono">O(B) memory pipeline</strong>. It demonstrates that dictionary compression (DEFLATE / LZMA) compresses repetitive data exponentially, meaning a 30% row increase with 20% size reduction is an explainable entropy phenomenon rather than corruption.
        </p>
      </section>

      {/* Four Core Pillars */}
      <section className="space-y-6">
        <div className="space-y-1">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400">
            Core Architecture
          </span>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            The Four Pillars of DBGuard
          </h2>
          <p className="text-sm text-slate-400">
            Engineered to provide mathematical guarantees without requiring duplicate database clusters.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 space-y-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950 text-cyan-400 border border-cyan-800">
              <Zap className="h-5 w-5" />
            </div>
            <h3 className="text-base font-bold text-white">1. Streaming Decompression</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Operates in a fixed 64 KB read buffer. Analyzes multi-gigabyte exports with sub-megabyte heap allocation (<span className="font-mono text-cyan-300">0.58 MB</span> RAM).
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 space-y-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950 text-cyan-400 border border-cyan-800">
              <Lock className="h-5 w-5" />
            </div>
            <h3 className="text-base font-bold text-white">2. Cryptographic Evidence</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Calculates whole-file SHA-256, uncompressed stream digest, 1MB chunk hashes, and domain-separated Merkle tree roots for localized proof paths.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 space-y-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950 text-cyan-400 border border-cyan-800">
              <Layers className="h-5 w-5" />
            </div>
            <h3 className="text-base font-bold text-white">3. Schema & Anomaly Rules</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              14 deterministic anomaly rules and robust historical Median Absolute Deviation (MAD) statistics distinguish entropy shifts from actual corruption.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 space-y-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950 text-cyan-400 border border-cyan-800">
              <Activity className="h-5 w-5" />
            </div>
            <h3 className="text-base font-bold text-white">4. Recovery Feasibility</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Translates technical checks into 6 standardized recovery classifications with recoverable record estimates and DBA next steps.
            </p>
          </div>
        </div>
      </section>

      {/* Workflow Step-by-Step */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-8 space-y-6">
        <div className="space-y-1">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400">
            How It Works
          </span>
          <h2 className="text-xl md:text-2xl font-bold tracking-tight text-white">
            The Single-Pass Inspection Pipeline
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2">
          <div className="relative rounded-xl border border-slate-800 bg-slate-950/70 p-5 space-y-2">
            <span className="text-xs font-mono font-bold text-cyan-400">STEP 01</span>
            <h4 className="text-sm font-bold text-white">Intake Inspection</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Verifies magic byte headers (gzip, bz2, xz) and computes compressed SHA-256 without decompression.
            </p>
          </div>

          <div className="relative rounded-xl border border-slate-800 bg-slate-950/70 p-5 space-y-2">
            <span className="text-xs font-mono font-bold text-cyan-400">STEP 02</span>
            <h4 className="text-sm font-bold text-white">Streaming Tapper</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Streams uncompressed chunks into SHA-256 hashers and 1MB chunk partitioners simultaneously.
            </p>
          </div>

          <div className="relative rounded-xl border border-slate-800 bg-slate-950/70 p-5 space-y-2">
            <span className="text-xs font-mono font-bold text-cyan-400">STEP 03</span>
            <h4 className="text-sm font-bold text-white">Incremental Parsing</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              CSV/SQL tokenizer counts records, handles quoted newlines, infers data types, and derives schema fingerprints.
            </p>
          </div>

          <div className="relative rounded-xl border border-slate-800 bg-slate-950/70 p-5 space-y-2">
            <span className="text-xs font-mono font-bold text-cyan-400">STEP 04</span>
            <h4 className="text-sm font-bold text-white">Audit & Publishing</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Verifies manifests, evaluates anomaly rules, classifies recovery status, and publishes PDF/JSON audit reports.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
