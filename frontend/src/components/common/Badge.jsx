import React from 'react';

export const Badge = ({ children, variant = 'default', className = '' }) => {
  const variantStyles = {
    default: 'bg-slate-800 text-slate-300 border-slate-700',
    primary: 'bg-blue-900/40 text-blue-400 border-blue-800/60',
    accent: 'bg-cyan-900/40 text-cyan-400 border-cyan-800/60',
    success: 'bg-emerald-950/60 text-emerald-400 border-emerald-800/50',
    warning: 'bg-amber-950/60 text-amber-400 border-amber-800/50',
    danger: 'bg-rose-950/60 text-rose-400 border-rose-800/50',
    // Congestion severity badges
    low: 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60',
    moderate: 'bg-amber-950/80 text-amber-300 border-amber-700/60',
    high: 'bg-orange-950/80 text-orange-300 border-orange-700/60',
    severe: 'bg-rose-950/80 text-rose-300 border-rose-700/60',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${variantStyles[variant] || variantStyles.default} ${className}`}
    >
      {children}
    </span>
  );
};

export const CongestionBadge = ({ percentage }) => {
  if (percentage === null || percentage === undefined) {
    return <Badge variant="default">N/A</Badge>;
  }

  const val = Number(percentage);
  if (val <= 25) {
    return <Badge variant="low">{val.toFixed(1)}% · Low</Badge>;
  } else if (val <= 50) {
    return <Badge variant="moderate">{val.toFixed(1)}% · Moderate</Badge>;
  } else if (val <= 75) {
    return <Badge variant="high">{val.toFixed(1)}% · High</Badge>;
  } else {
    return <Badge variant="severe">{val.toFixed(1)}% · Severe</Badge>;
  }
};
