import React from 'react';

export const Card = ({
  title,
  subtitle,
  action,
  children,
  className = '',
  headerClassName = '',
  bodyClassName = '',
  footer,
}) => {
  return (
    <div className={`bg-[#111827] border border-slate-800/80 rounded-xl shadow-lg shadow-black/20 overflow-hidden flex flex-col ${className}`}>
      {(title || subtitle || action) && (
        <div className={`px-5 py-4 border-b border-slate-800/80 flex items-center justify-between gap-4 ${headerClassName}`}>
          <div>
            {title && <h3 className="text-base font-semibold text-slate-100">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div className="flex-shrink-0">{action}</div>}
        </div>
      )}
      <div className={`p-5 flex-1 ${bodyClassName}`}>{children}</div>
      {footer && (
        <div className="px-5 py-3 bg-slate-900/60 border-t border-slate-800/80 text-xs text-slate-400">
          {footer}
        </div>
      )}
    </div>
  );
};

export const MetricCard = ({
  title,
  value,
  unit = '',
  change = null,
  isPositiveGood = false,
  icon: Icon,
  description,
  accentColor = 'cyan', // cyan, blue, emerald, amber, rose
  className = '',
}) => {
  const accentClasses = {
    cyan: 'border-cyan-500/30 text-cyan-400 bg-cyan-950/20',
    blue: 'border-blue-500/30 text-blue-400 bg-blue-950/20',
    emerald: 'border-emerald-500/30 text-emerald-400 bg-emerald-950/20',
    amber: 'border-amber-500/30 text-amber-400 bg-amber-950/20',
    rose: 'border-rose-500/30 text-rose-400 bg-rose-950/20',
  };

  return (
    <div className={`bg-[#111827] border border-slate-800/90 rounded-xl p-5 hover:border-slate-700 transition-colors shadow-md shadow-black/10 ${className}`}>
      <div className="flex items-start justify-between">
        <div>
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">{title}</span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold tracking-tight text-slate-50 font-mono">{value}</span>
            {unit && <span className="text-xs font-medium text-slate-400">{unit}</span>}
          </div>
        </div>
        {Icon && (
          <div className={`p-2.5 rounded-lg border ${accentClasses[accentColor] || accentClasses.cyan}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      {(change !== null || description) && (
        <div className="mt-3 flex items-center justify-between text-xs pt-3 border-t border-slate-800/60">
          {change !== null && (
            <span
              className={`font-semibold ${
                change > 0
                  ? isPositiveGood
                    ? 'text-emerald-400'
                    : 'text-rose-400'
                  : change < 0
                  ? isPositiveGood
                    ? 'text-rose-400'
                    : 'text-emerald-400'
                  : 'text-slate-400'
              }`}
            >
              {change > 0 ? `+${change}%` : `${change}%`} vs baseline
            </span>
          )}
          {description && <span className="text-slate-400 truncate ml-auto">{description}</span>}
        </div>
      )}
    </div>
  );
};
