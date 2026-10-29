import React from 'react';
import { GrievanceStatus, GrievancePriority } from '../../types';
import { AlertCircle, CheckCircle2, Clock, Eye, FileText, RefreshCw, XCircle } from 'lucide-react';

export const StatusBadge: React.FC<{ status: GrievanceStatus; className?: string }> = ({ status, className = '' }) => {
  switch (status) {
    case 'SUBMITTED':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200 ${className}`}>
          <Clock className="w-3.5 h-3.5 text-blue-500" />
          Submitted
        </span>
      );
    case 'UNDER_REVIEW':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200 ${className}`}>
          <Eye className="w-3.5 h-3.5 text-indigo-500" />
          Under Review
        </span>
      );
    case 'NEEDS_INFORMATION':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200 ${className}`}>
          <AlertCircle className="w-3.5 h-3.5 text-amber-500" />
          Needs Info
        </span>
      );
    case 'ASSIGNED':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-purple-50 text-purple-700 border border-purple-200 ${className}`}>
          <FileText className="w-3.5 h-3.5 text-purple-500" />
          Assigned
        </span>
      );
    case 'INVESTIGATION_IN_PROGRESS':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-cyan-50 text-cyan-700 border border-cyan-200 ${className}`}>
          <RefreshCw className="w-3.5 h-3.5 text-cyan-500 animate-spin" />
          Investigating
        </span>
      );
    case 'RESOLUTION_PROPOSED':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-teal-50 text-teal-700 border border-teal-200 ${className}`}>
          <CheckCircle2 className="w-3.5 h-3.5 text-teal-500" />
          Resolution Proposed
        </span>
      );
    case 'RESOLVED':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 ${className}`}>
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          Resolved
        </span>
      );
    case 'CLOSED':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200 ${className}`}>
          Closed
        </span>
      );
    case 'REOPENED':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-orange-50 text-orange-700 border border-orange-200 ${className}`}>
          <RefreshCw className="w-3.5 h-3.5 text-orange-500" />
          Reopened
        </span>
      );
    case 'ESCALATED':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-50 text-rose-700 border border-rose-300 ${className}`}>
          <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
          Escalated
        </span>
      );
    case 'REJECTED':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 border border-gray-300 ${className}`}>
          <XCircle className="w-3.5 h-3.5 text-gray-500" />
          Rejected
        </span>
      );
    default:
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-800 ${className}`}>
          {status}
        </span>
      );
  }
};

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
