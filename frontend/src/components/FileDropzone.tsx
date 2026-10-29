import React, { useRef, useState } from 'react';
import { UploadCloud, X, FileArchive } from 'lucide-react';

export interface FileDropzoneProps {
  label: string;
  description?: string;
  accept?: string;
  maxSizeMB?: number;
  file?: File | null;
  selectedFile?: File | null;
  onFileSelect: (file: File | null) => void;
  className?: string;
}

export const FileDropzone: React.FC<FileDropzoneProps> = ({
  label,
  description = 'Drag & drop compressed database export archive (.gz, .bz2, .xz, .csv)',
  accept = '.gz,.bz2,.xz,.zst,.csv,.jsonl,.sql',
  maxSizeMB = 500,
  file,
  selectedFile,
  onFileSelect,
  className = '',
}) => {
  const currentFile = file !== undefined ? file : selectedFile || null;
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={`w-full ${className}`}>
      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 font-mono">
        {label}
      </label>

      {currentFile ? (
        <div className="flex items-center justify-between rounded-2xl border border-cyan-800/80 bg-slate-900/80 p-4 transition-all">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950 border border-cyan-800 text-cyan-400">
              <FileArchive className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white truncate max-w-xs md:max-w-md">
                {currentFile.name}
              </p>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                {formatFileSize(currentFile.size)} &bull; Ready for streaming audit
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              onFileSelect(null);
              if (inputRef.current) inputRef.current.value = '';
            }}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
            title="Remove file"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ) : (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-7 text-center cursor-pointer transition-all ${
            isDragging
              ? 'border-cyan-500 bg-cyan-950/30 scale-[0.99]'
              : 'border-slate-800 bg-slate-900/30 hover:border-slate-700 hover:bg-slate-900/60'
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept={accept}
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                onFileSelect(e.target.files[0]);
              }
            }}
            className="hidden"
          />
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-800 text-cyan-400 mb-3 group-hover:scale-105 transition-transform">
            <UploadCloud className="h-6 w-6" />
          </div>
          <p className="text-sm font-semibold text-slate-200">
            Click to upload or drag & drop export
          </p>
          <p className="text-xs text-slate-400 mt-1 max-w-sm">{description}</p>
          <div className="mt-3 flex items-center gap-1.5 text-[10px] text-slate-500 font-mono">
            <span className="rounded bg-slate-800 px-1.5 py-0.5 text-slate-300">.gz</span>
            <span className="rounded bg-slate-800 px-1.5 py-0.5 text-slate-300">.bz2</span>
            <span className="rounded bg-slate-800 px-1.5 py-0.5 text-slate-300">.xz</span>
            <span className="rounded bg-slate-800 px-1.5 py-0.5 text-slate-300">.csv</span>
            <span className="rounded bg-slate-800 px-1.5 py-0.5 text-slate-300">.sql</span>
            <span>&bull; Max {maxSizeMB} MB</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileDropzone;
