import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  ShieldCheck,
  LayoutDashboard,
  FileSearch,
  GitCompare,
  FileCheck2,
  FileSignature,
  HeartPulse,
  LineChart,
  FileText,
  Info,
  GraduationCap,
  Sparkles,
  ExternalLink
} from 'lucide-react';

interface NavItem {
  label: string;
  to: string;
  icon: any;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Overview', to: '/', icon: Sparkles },
  { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { label: 'Analyze Export', to: '/analyze', icon: FileSearch },
  { label: 'Compare Exports', to: '/compare', icon: GitCompare },
  { label: 'Integrity Evidence', to: '/evidence', icon: FileCheck2 },
  { label: 'Manifest Manager', to: '/manifest', icon: FileSignature },
  { label: 'Recovery Assessment', to: '/recovery', icon: HeartPulse },
  { label: 'Reports Download', to: '/reports', icon: FileText },
  { label: 'Benchmarks & Scalability', to: '/benchmarks', icon: LineChart },
  { label: 'System Architecture', to: '/about', icon: Info },
];

export const AppSidebar: React.FC = () => {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-slate-900 border-r border-slate-800 text-slate-300 transition-all">
      {/* Brand Header */}
      <div className="flex h-16 items-center gap-3 border-b border-slate-800/80 px-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-indigo-600 text-white shadow-md shadow-brand-500/20">
          <ShieldCheck className="h-6 w-6" />
        </div>
        <div>
          <div className="flex items-center gap-1.5 font-bold text-white text-base tracking-tight font-sans">
            DBGuard
            <span className="rounded bg-brand-500/20 px-1.5 py-0.2 text-[10px] font-semibold text-brand-300 border border-brand-500/30">
              v1.0
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-medium">Export Integrity Analyzer</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4 text-sm font-medium scrollbar-thin scrollbar-thumb-slate-800">
        <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          Core Workflows
        </div>

        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `group flex items-center justify-between rounded-lg px-3 py-2.5 transition-all ${
                  isActive
                    ? 'bg-brand-600/20 text-white border-l-2 border-brand-500 font-semibold'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-100'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="h-4 w-4 shrink-0 transition-colors group-hover:text-brand-400" />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-300 border border-emerald-500/30">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer Info Box */}
      <div className="border-t border-slate-800/80 p-4">
        <div className="rounded-xl bg-slate-850/80 p-3 border border-slate-800 text-xs">
          <div className="flex items-center justify-between text-slate-300 font-medium mb-1">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              Engine Online
            </span>
            <span className="font-mono text-[10px] text-slate-400">O(B) Stream</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Zero secondary database restore required. Single-pass bounded memory.
          </p>
          <a
            href="https://github.com/jayshinde286-source/hackthon"
            target="_blank"
            rel="noreferrer"
            className="mt-2.5 flex items-center justify-center gap-1.5 rounded-lg bg-slate-800 px-2 py-1 text-[11px] font-medium text-slate-300 transition-colors hover:bg-slate-700 hover:text-white"
          >
            <span>GitHub Repository</span>
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>
    </aside>
  );
};

