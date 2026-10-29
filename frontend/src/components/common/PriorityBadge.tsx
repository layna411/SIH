import React from 'react';
import { GrievancePriority } from '../../types';

export const PriorityBadge: React.FC<{ priority: GrievancePriority; className?: string }> = ({ priority, className = '' }) => {
  switch (priority) {
    case 'URGENT':
      return (
        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-200 ${className}`}>
          <span className="w-1.5 h-1.5 rounded-full bg-rose-600 animate-pulse"></span>
          Urgent
        </span>
      );
    case 'HIGH':
      return (
        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200 ${className}`}>
          <span className="w-1.5 h-1.5 rounded-full bg-amber-600"></span>
          High
        </span>
      );
    case 'NORMAL':
      return (
        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200 ${className}`}>
          Normal
        </span>
      );
    case 'LOW':
      return (
        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200 ${className}`}>
          Low
        </span>
      );
    default:
      return null;
  }
};
