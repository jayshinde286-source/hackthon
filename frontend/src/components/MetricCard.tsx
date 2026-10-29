import React from 'react';

export interface MetricCardProps {
  title?: string;
  label?: string;
  value: string | number;
  subtitle?: string;
  description?: string;
  icon?: React.ReactNode;
  badge?: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger';
  trend?: {
    value: string;
    isPositive?: boolean;
    isNeutral?: boolean;
  };
  onClick?: () => void;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  label,
  value,
  subtitle,
  description,
  icon,
  badge,
  variant = 'default',
  trend,
  onClick,
  className = '',
}) => {
  const displayTitle = label || title || '';
  const displaySubtitle = description || subtitle;

  let borderColor = 'border-slate-800';
  let valueColor = 'text-white';
  let iconBg = 'bg-slate-800/60 text-cyan-400 border-slate-700/60';

  if (variant === 'success') {
    borderColor = 'border-emerald-800/50';
    valueColor = 'text-emerald-400';
    iconBg = 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60';
  } else if (variant === 'warning') {
    borderColor = 'border-amber-800/50';
    valueColor = 'text-amber-400';
    iconBg = 'bg-amber-950/60 text-amber-400 border-amber-800/60';
  } else if (variant === 'danger') {
    borderColor = 'border-rose-800/50';
    valueColor = 'text-rose-400';
    iconBg = 'bg-rose-950/60 text-rose-400 border-rose-800/60';
  }

  return (
    <div
      onClick={onClick}
      className={`relative overflow-hidden rounded-2xl border ${borderColor} bg-slate-900/50 p-5 backdrop-blur transition-all duration-200 hover:border-slate-700 shadow-sm ${
        onClick ? 'cursor-pointer hover:bg-slate-800/40' : ''
      } ${className}`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
          {displayTitle}
        </span>
        {icon && (
          <div className={`flex h-9 w-9 items-center justify-center rounded-xl border ${iconBg}`}>
            {icon}
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span className={`text-2xl font-bold tracking-tight font-mono ${valueColor}`}>
          {value}
        </span>
        {badge}
      </div>

      {(displaySubtitle || trend) && (
        <div className="mt-2 flex items-center justify-between text-xs text-slate-400 font-sans">
          {displaySubtitle && <span>{displaySubtitle}</span>}
          {trend && (
            <span
              className={`font-semibold ${
                trend.isNeutral
                  ? 'text-slate-400'
                  : trend.isPositive
                  ? 'text-emerald-400'
                  : 'text-rose-400'
              }`}
            >
              {trend.value}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default MetricCard;
