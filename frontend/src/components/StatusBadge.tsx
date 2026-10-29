import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, HelpCircle, ShieldCheck } from 'lucide-react';
import { VerificationStatus, RecoveryClassification } from '../types';

interface StatusBadgeProps {
  status: VerificationStatus | RecoveryClassification | string;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md', showIcon = true }) => {
  const s = String(status).toUpperCase();

  let bg = 'bg-slate-100 text-slate-800 border-slate-200';
  let icon = <HelpCircle className="w-3.5 h-3.5" />;

  if (s === 'PASS' || s === 'VERIFIED_WITHIN_SCOPE') {
    bg = 'bg-emerald-50 text-emerald-700 border-emerald-200';
    icon = <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />;
  } else if (
    s === 'WARNING' ||
    s === 'LIKELY_USABLE_BUT_NOT_FULLY_VERIFIED' ||
    s === 'RECOVERY_POSSIBLE_WITH_ERRORS'
  ) {
    bg = 'bg-amber-50 text-amber-800 border-amber-200';
    icon = <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />;
  } else if (s === 'FAIL' || s === 'INTEGRITY_FAILURE') {
    bg = 'bg-rose-50 text-rose-700 border-rose-200';
    icon = <XCircle className="w-3.5 h-3.5 text-rose-600" />;
  } else if (s === 'INCONCLUSIVE' || s === 'UNSUPPORTED_FORMAT') {
    bg = 'bg-blue-50 text-blue-700 border-blue-200';
    icon = <HelpCircle className="w-3.5 h-3.5 text-blue-600" />;
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5 font-medium',
    lg: 'text-sm px-3.5 py-1.5 gap-2 font-semibold',
  };

  return (
    <span
      className={`inline-flex items-center rounded-md border tracking-wide uppercase transition-colors ${bg} ${sizeClasses[size]}`}
    >
      {showIcon && icon}
      <span>{s.replace(/_/g, ' ')}</span>
    </span>
  );
};

export default StatusBadge;
