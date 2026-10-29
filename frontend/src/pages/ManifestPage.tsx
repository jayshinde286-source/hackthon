import React, { useState } from 'react';
import { 
  FileCheck, 
  UploadCloud, 
  Key, 
  Download, 
  CheckCircle2, 
  AlertTriangle, 
  ShieldAlert, 
  FileJson,
  Layers
} from 'lucide-react';
import { api } from '../api/client';
import FileDropzone from '../components/FileDropzone';

export const ManifestPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'validate' | 'generate'>('validate');

  // Validate state
  const [validateManifestFile, setValidateManifestFile] = useState<File | null>(null);
  const [validateLoading, setValidateLoading] = useState(false);
  const [validateError, setValidateError] = useState<string | null>(null);
  const [validationResult, setValidationResult] = useState<any | null>(null);

  // Generate state
  const [genExportFile, setGenExportFile] = useState<File | null>(null);
  const [sourceIdentifier, setSourceIdentifier] = useState('prod-db-cluster-01.primary');
  const [isTrusted, setIsTrusted] = useState(true);
  const [secretKey, setSecretKey] = useState('');
  const [genLoading, setGenLoading] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);
  const [generatedManifest, setGeneratedManifest] = useState<any | null>(null);

  const handleValidate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateManifestFile) {
      setValidateError('Please select a JSON manifest file to validate.');
      return;
    }
    try {
      setValidateLoading(true);
      setValidateError(null);
      const res = await api.validateManifest(validateManifestFile);
      setValidationResult(res);
    } catch (err: any) {
      setValidateError(err.message || 'Manifest validation failed.');
    } finally {
      setValidateLoading(false);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!genExportFile) {
      setGenError('Please select a compressed export file.');
      return;
    }
    try {
      setGenLoading(true);
      setGenError(null);
      const res = await api.generateManifest(
        genExportFile,
        sourceIdentifier,
        isTrusted,
        secretKey.trim() || undefined
      );
      setGeneratedManifest(res.manifest);
    } catch (err: any) {
      setGenError(err.message || 'Manifest generation failed.');
    } finally {
      setGenLoading(false);
    }
  };

  const downloadGeneratedJson = () => {
    if (!generatedManifest) return;
    const blob = new Blob([JSON.stringify(generatedManifest, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `manifest_${generatedManifest.export_metadata?.filename || 'export'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8 pb-16 max-w-4xl mx-auto">
      {/* Title */}
      <div className="border-b border-slate-800 pb-6">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <FileCheck className="w-8 h-8 text-cyan-400" />
          <span>Cryptographic Manifest Center</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Validate external backup manifests against Schema 1.0 or generate new cryptographically signed manifests.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800">
        <button
          onClick={() => setActiveTab('validate')}
          className={`px-5 py-2.5 text-sm font-semibold transition-all border-b-2 flex items-center gap-2 ${
            activeTab === 'validate'
              ? 'border-cyan-400 text-cyan-400 bg-cyan-950/20'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileJson className="w-4 h-4" />
          <span>Validate Existing Manifest</span>
        </button>
        <button
          onClick={() => setActiveTab('generate')}
          className={`px-5 py-2.5 text-sm font-semibold transition-all border-b-2 flex items-center gap-2 ${
            activeTab === 'generate'
              ? 'border-cyan-400 text-cyan-400 bg-cyan-950/20'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Generate New Signed Manifest</span>
        </button>
      </div>

      {/* TAB 1: VALIDATE */}
      {activeTab === 'validate' && (
        <div className="space-y-6">
          {validateError && (
            <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/50 text-red-300 text-sm flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 flex-shrink-0 text-red-400" />
              <span>{validateError}</span>
            </div>
          )}

          <form onSubmit={handleValidate} className="space-y-6">
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-slate-200">
                Upload Manifest File (.json)
              </label>
              <FileDropzone
                file={validateManifestFile}
                onFileSelect={setValidateManifestFile}
                accept=".json"
                label="Select JSON manifest to inspect"
                description="Checks Schema 1.0 compliance, checksum formatting, and provenance classification."
              />
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={!validateManifestFile || validateLoading}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-sm transition-all shadow-md shadow-cyan-500/20 disabled:opacity-50"
              >
                {validateLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                    <span>Verifying Schema & Hashes...</span>
                  </>
                ) : (
                  <>
                    <FileCheck className="w-4 h-4" />
                    <span>Validate Manifest</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {validationResult && (
            <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs uppercase font-mono tracking-wider font-semibold text-cyan-400">
                  Schema 1.0 Validation Result
                </span>
                <span
                  className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold ${
                    validationResult.valid
                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                      : 'bg-rose-950 text-rose-400 border border-rose-800'
                  }`}
                >
                  {validationResult.valid ? 'VALID SCHEMA' : 'INVALID SCHEMA'}
                </span>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs space-y-2 text-slate-300">
                <div className="flex justify-between">
                  <span className="text-slate-500">Manifest Version:</span>
                  <span className="text-cyan-300">{validationResult.manifest?.schema_version || '1.0'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Provenance:</span>
                  <span className="text-white">{validationResult.manifest?.provenance?.type || 'OBSERVATIONAL'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Declared Record Count:</span>
                  <span className="text-white">{validationResult.manifest?.export_metadata?.row_count?.toLocaleString() || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Physical SHA-256:</span>
                  <span className="text-cyan-400 break-all">{validationResult.manifest?.checksums?.compressed_sha256 || 'N/A'}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: GENERATE */}
      {activeTab === 'generate' && (
        <div className="space-y-6">
          {genError && (
            <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/50 text-red-300 text-sm flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 flex-shrink-0 text-red-400" />
              <span>{genError}</span>
            </div>
          )}

          <form onSubmit={handleGenerate} className="space-y-6">
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-slate-200">
                1. Select Compressed Database Export Archive <span className="text-cyan-400">*</span>
              </label>
              <FileDropzone
                file={genExportFile}
                onFileSelect={setGenExportFile}
                accept=".gz,.bz2,.xz,.csv,.sql"
                label="Upload export archive to compute manifest hashes"
                description="Calculates row counts, physical and logical SHA-256, and chunk hashes in bounded memory."
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-5 rounded-2xl border border-slate-800 bg-slate-900/40">
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-300 uppercase font-mono tracking-wider">
                  Source Database Identifier
                </label>
                <input
                  type="text"
                  value={sourceIdentifier}
                  onChange={(e) => setSourceIdentifier(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-300 uppercase font-mono tracking-wider">
                  Provenance Mode
                </label>
                <select
                  value={isTrusted ? 'trusted' : 'post_hoc'}
                  onChange={(e) => setIsTrusted(e.target.value === 'trusted')}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="trusted">TRUSTED_EXPORT_PIPELINE (Primary authority)</option>
                  <option value="post_hoc">OBSERVATIONAL_POST_HOC (Post-export inspection)</option>
                </select>
              </div>

              <div className="md:col-span-2 space-y-1.5 pt-2">
                <label className="block text-xs font-semibold text-slate-300 uppercase font-mono tracking-wider flex items-center gap-1.5">
                  <Key className="w-3.5 h-3.5 text-cyan-400" />
                  HMAC Authentication Secret (Optional)
                </label>
                <input
                  type="password"
                  placeholder="Optional secret to sign the manifest with HMAC-SHA256"
                  value={secretKey}
                  onChange={(e) => setSecretKey(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder:text-slate-600 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={!genExportFile || genLoading}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-sm transition-all shadow-md shadow-cyan-500/20 disabled:opacity-50"
              >
                {genLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                    <span>Streaming & Hashing Stream...</span>
                  </>
                ) : (
                  <>
                    <Layers className="w-4 h-4" />
                    <span>Generate Manifest JSON</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {generatedManifest && (
            <div className="p-6 rounded-2xl border border-emerald-900/50 bg-slate-900/60 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  <span className="text-sm font-semibold text-white">
                    Manifest Generated Successfully
                  </span>
                </div>
                <button
                  onClick={downloadGeneratedJson}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs transition-colors shadow-sm"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download Manifest JSON
                </button>
              </div>

              <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-[11px] text-cyan-300 max-h-72 overflow-y-auto">
                {JSON.stringify(generatedManifest, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

