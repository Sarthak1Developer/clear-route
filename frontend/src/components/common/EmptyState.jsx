import React from 'react';
import { AlertCircle, Database, HelpCircle } from 'lucide-react';

export const EmptyState = ({
  title = 'No Data Available',
  message = 'No records match the requested parameters or the corridor lacks sensor coverage for this time range.',
  reason = null,
  action = null,
  icon: Icon = AlertCircle,
  className = '',
}) => {
  return (
    <div className={`flex flex-col items-center justify-center p-8 my-4 text-center bg-slate-900/40 border border-dashed border-slate-800 rounded-xl ${className}`}>
      <div className="p-3 bg-slate-800/80 rounded-full text-slate-400 mb-3 border border-slate-700">
        <Icon className="w-6 h-6" />
      </div>
      <h4 className="text-base font-semibold text-slate-200 mb-1">{title}</h4>
      <p className="text-xs text-slate-400 max-w-md mb-3">{message}</p>
      
      {reason && (
        <div className="bg-slate-950/80 border border-slate-800/80 px-3 py-2 rounded text-xs text-amber-400/90 max-w-lg mb-4 text-left flex items-start gap-2">
          <HelpCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-400" />
          <span><strong>Dataset Coverage Boundary:</strong> {reason}</span>
        </div>
      )}

      {action && <div>{action}</div>}
    </div>
  );
};
