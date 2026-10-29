import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  UploadCloud, 
  FileCheck, 
  Key, 
  HelpCircle, 
  ArrowRight, 
  FileCode,
  AlertCircle
} from 'lucide-react';
import { api } from '../api/client';
import FileDropzone from '../components/FileDropzone';

export const AnalyzePage: React.FC = () => {
  const navigate = useNavigate();
  const [exportFile, setExportFile] = useState<File | null>(null);
  const [manifestFile, setManifestFile] = useState<File | null>(null);
  const [dataFormat, setDataFormat] = useState<string>('auto');
  const [secretKey, setSecretKey] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!exportFile) {
      setError('Please select a compressed database export file.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const result = await api.uploadAnalysis(
        exportFile,
        manifestFile,
        dataFormat === 'auto' ? undefined : dataFormat,
        secretKey.trim() ? secretKey.trim() : undefined
      );
      navigate(`/analysis/${result.summary.id}`);
    } catch (err: any) {
      setError(err.message || 'Analysis failed. Please verify the archive stream.');
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      {/* Page Title */}
      <div className="border-b border-slate-800 pb-6">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <UploadCloud className="w-8 h-8 text-cyan-400" />
          <span>Inspect Compressed Export</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Perform a single-pass, bounded-memory integrity audit on a compressed database export without secondary restoration.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/50 text-red-300 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-400 mt-0.5" />
          <div>
            <span className="font-semibold block">Execution Error</span>
            <span className="text-xs text-red-300/80">{error}</span>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Step 1: Export Archive */}
        <div className="space-y-3">
          <label className="block text-sm font-semibold text-slate-200">
            1. Compressed Database Export File <span className="text-cyan-400">*</span>
          </label>
          <FileDropzone
            file={exportFile}
            onFileSelect={setExportFile}
            accept=".gz,.bz2,.xz,.csv,.sql"
            label="Upload compressed export archive (.gz, .bz2, .xz) or raw dump"
            description="Supports Gzip, Bzip2, and XZ streaming formats. Processed entirely in bounded RAM."
          />
        </div>

        {/* Step 2: Optional Manifest */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <FileCheck className="w-4 h-4 text-emerald-400" />
              <span>2. Trusted Export Manifest (Optional)</span>
            </label>
            <span className="text-xs text-slate-500 font-mono">Schema 1.0 JSON</span>
          </div>
          <FileDropzone
            file={manifestFile}
            onFileSelect={setManifestFile}
            accept=".json"
            label="Attach cryptographic manifest metadata (.json)"
            description="If provided, DBGuard cryptographically validates expected row counts, byte sizes, and SHA-256 hashes."
          />
        </div>

        {/* Configuration Options */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 rounded-2xl border border-slate-800 bg-slate-900/50">
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono">
              Data Format Parser
            </label>
            <select
              value={dataFormat}
              onChange={(e) => setDataFormat(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-cyan-500 transition-colors"
            >
              <option value="auto">Auto-Detect Stream Structure</option>
              <option value="csv">Delimited / CSV Stream</option>
              <option value="sql">SQL Dump Statements (INSERT INTO)</option>
            </select>
            <p className="text-[11px] text-slate-500">
              Auto-detect inspects magic numbers, headers, and statement signatures on the initial byte buffer.
            </p>
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
              <Key className="w-3.5 h-3.5 text-cyan-400" />
              HMAC Secret Key (Optional)
            </label>
            <input
              type="password"
              placeholder="Enter secret for HMAC verification"
              value={secretKey}
              onChange={(e) => setSecretKey(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500 transition-colors font-mono"
            />
            <p className="text-[11px] text-slate-500">
              Only required if your manifest was generated with HMAC-SHA256 authentication.
            </p>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex items-center justify-between pt-4">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <HelpCircle className="w-4 h-4 text-cyan-400" />
            <span>RAM allocation remains under 2 MB regardless of dump size.</span>
          </div>

          <button
            type="submit"
            disabled={!exportFile || loading}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-semibold text-sm transition-all shadow-lg shadow-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                <span>Streaming & Auditing Export...</span>
              </>
            ) : (
              <>
                <span>Start Stream Analysis</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>

      {/* Info Callout */}
      <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-5 space-y-2 text-xs text-slate-400">
        <h4 className="font-semibold text-slate-200 flex items-center gap-2">
          <FileCode className="w-4 h-4 text-cyan-400" />
          Single-Pass Verification Architecture
        </h4>
        <p className="leading-relaxed">
          DBGuard passes the compressed byte stream through a sliding 64 KB decompression window. While verifying CRC32 / Adler32 checksums inside the container headers, it computes SHA-256 digests on both the physical stream and uncompressed records simultaneously.
        </p>
      </div>
    </div>
  );
};
