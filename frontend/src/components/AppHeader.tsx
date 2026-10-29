import React from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { Shield, PlusCircle, Github } from 'lucide-react';

export const AppHeader: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const getBreadcrumb = () => {
    const path = location.pathname;
    if (path === '/') return 'Overview & Mission';
    if (path.startsWith('/dashboard')) return 'Operational Dashboard';
    if (path.startsWith('/analyze')) return 'Streaming Export Analysis';
    if (path.startsWith('/analysis')) return 'Analysis Inspection';
    if (path.startsWith('/compare')) return 'Export Comparative Analysis';
    if (path.startsWith('/evidence')) return 'Granular Integrity Evidence';
    if (path.startsWith('/manifest')) return 'Integrity Manifest Manager';
    if (path.startsWith('/recovery')) return 'Data Recovery Feasibility';
    if (path.startsWith('/reports')) return 'Audit Report Publishing';
    if (path.startsWith('/benchmarks')) return 'Empirical Benchmarks';
    if (path.startsWith('/about')) return 'Architecture & Methodology';
    if (path.startsWith('/viva-guide')) return 'Viva Examination Guide';
    return 'DBGuard';
  };

  return (
    <header className="sticky top-0 z-20 flex h-16 w-full items-center justify-between border-b border-slate-800 bg-slate-900/90 px-8 backdrop-blur-md">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Link to="/" className="hover:text-cyan-400 transition-colors">
            DBGuard
          </Link>
          <span className="text-slate-600">/</span>
          <span className="font-semibold text-white">{getBreadcrumb()}</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <span className="hidden md:inline-flex items-center gap-1.5 rounded-full bg-slate-800/80 px-3 py-1 text-xs font-mono font-medium text-cyan-300 border border-slate-700">
          <Shield className="h-3.5 w-3.5 text-cyan-400" />
          Bounded O(B) Engine
        </span>

        <button
          onClick={() => navigate('/analyze')}
          className="inline-flex items-center gap-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 px-3.5 py-1.5 text-xs font-semibold text-slate-950 shadow-sm shadow-cyan-500/20 transition-all active:scale-95"
        >
          <PlusCircle className="h-3.5 w-3.5" />
          <span>New Analysis</span>
        </button>

        <a
          href="https://github.com/jayshinde286-source/hackthon"
          target="_blank"
          rel="noreferrer"
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-800 bg-slate-800/60 text-slate-300 transition-colors hover:bg-slate-800 hover:text-white"
          title="View on GitHub"
        >
          <Github className="h-4 w-4" />
        </a>
      </div>
    </header>
  );
};
