import React from 'react';

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const s = status.toUpperCase();
  let color = 'bg-slate-800 text-slate-300 border-slate-700';

  if (s === 'COMPLETED' || s === 'EXECUTED' || s === 'APPROVED' || s === 'SUCCESS') {
    color = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  } else if (s === 'SCHEDULED' || s === 'PROPOSED') {
    color = 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
  } else if (s === 'IN_PROGRESS' || s === 'PENDING') {
    color = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
  } else if (s === 'FAILED' || s === 'REJECTED' || s === 'CANCELLED') {
    color = 'bg-rose-500/10 text-rose-400 border-rose-500/30';
  } else if (s === 'REPLANNED') {
    color = 'bg-purple-500/10 text-purple-400 border-purple-500/30';
  }

  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${color}`}>
      {status}
    </span>
  );
};
