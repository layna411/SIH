import React from 'react';
import { CaseAction } from '../../types';
import { 
  FileText, 
  UserCheck, 
  Search, 
  Send, 
  MessageSquare, 
  Users, 
  Calendar, 
  CheckCircle2, 
  ArrowRightLeft, 
  TrendingUp, 
  ShieldAlert, 
  Clock,
  FileCheck
} from 'lucide-react';

interface ProceduralActionLogProps {
  actions: CaseAction[];
}

export const ProceduralActionLog: React.FC<ProceduralActionLogProps> = ({ actions }) => {
  const getActionIcon = (actionType: string) => {
    switch (actionType) {
      case 'INTAKE':
        return <FileCheck className="w-4 h-4 text-emerald-600" />;
      case 'ASSIGNMENT':
        return <UserCheck className="w-4 h-4 text-blue-600" />;
      case 'INITIAL_SCRUTINY':
        return <Search className="w-4 h-4 text-indigo-600" />;
      case 'INFO_REQUESTED':
        return <Send className="w-4 h-4 text-amber-600" />;
      case 'EXPLANATION_RECEIVED':
        return <MessageSquare className="w-4 h-4 text-sky-600" />;
      case 'COMMITTEE_REVIEW':
        return <Users className="w-4 h-4 text-purple-600" />;
      case 'HEARING_SCHEDULED':
      case 'HEARING_COMPLETED':
        return <Calendar className="w-4 h-4 text-violet-600" />;
      case 'COMPLIANCE_VERIFIED':
        return <CheckCircle2 className="w-4 h-4 text-teal-600" />;
      case 'TRANSFER_INITIATED':
      case 'TRANSFER_ACCEPTED':
        return <ArrowRightLeft className="w-4 h-4 text-orange-600" />;
      case 'ESCALATION':
        return <TrendingUp className="w-4 h-4 text-rose-600" />;
      case 'DISPOSAL_ORDER':
        return <ShieldAlert className="w-4 h-4 text-emerald-700" />;
      default:
        return <FileText className="w-4 h-4 text-slate-600" />;
    }
  };

  const getStatusBadge = (status?: string) => {
    if (!status) return null;
    const styles: Record<string, string> = {
      RECEIVED: 'bg-slate-100 text-slate-700 border-slate-200',
      PENDING_REVIEW: 'bg-amber-50 text-amber-700 border-amber-200',
      UNDER_PROCESS: 'bg-blue-50 text-blue-700 border-blue-200',
      AWAITING_RESPONSE: 'bg-yellow-50 text-yellow-700 border-yellow-200',
      TRANSFER_PENDING: 'bg-orange-50 text-orange-700 border-orange-200',
      TRANSFERRED: 'bg-orange-100 text-orange-800 border-orange-300',
      ESCALATED: 'bg-rose-50 text-rose-700 border-rose-200',
      DISPOSED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      CLOSED: 'bg-slate-100 text-slate-800 border-slate-300',
      REOPENED: 'bg-purple-50 text-purple-700 border-purple-200',
    };
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium border ${styles[status] || 'bg-slate-100 text-slate-700'}`}>
        {status.replace('_', ' ')}
      </span>
    );
  };

  if (!actions || actions.length === 0) {
    return (
      <div className="py-8 text-center text-slate-500 text-sm">
        No procedural actions recorded yet.
      </div>
    );
  }

  return (
    <div className="flow-root">
      <ul className="-mb-8">
        {actions.map((action, idx) => (
          <li key={action.id || idx}>
            <div className="relative pb-8">
              {idx !== actions.length - 1 && (
                <span
                  className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-slate-200"
                  aria-hidden="true"
                />
              )}
              <div className="relative flex space-x-3 items-start">
                <div className="h-8 w-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center ring-8 ring-white shrink-0">
                  {getActionIcon(action.action_type)}
                </div>
                <div className="min-w-0 flex-1 pt-0.5">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold text-slate-800">
                        {action.action_title}
                      </p>
                      <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                        {action.action_type.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <time className="text-xs text-slate-400">
                      {new Date(action.action_at).toLocaleString()}
                    </time>
                  </div>

                  {/* Performed by & Unit */}
                  <div className="text-xs text-slate-500 mt-1 flex flex-wrap items-center gap-3">
                    <span>
                      Actor: <strong className="text-slate-700">{action.performed_by_name || 'Authorized Officer'}</strong>
                    </span>
                    {action.unit_code && (
                      <span className="inline-flex items-center gap-1 font-medium text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                        Bureau: {action.unit_code}
                      </span>
                    )}
                  </div>

                  {/* Status Transition indicator if applicable */}
                  {action.new_status && action.previous_status && action.new_status !== action.previous_status && (
                    <div className="mt-2 text-xs flex items-center gap-2 text-slate-600 bg-slate-50 border border-slate-200/80 rounded-lg p-2">
                      <span className="text-slate-500 font-medium">Status Change:</span>
                      {getStatusBadge(action.previous_status)}
                      <span className="text-slate-400">➔</span>
                      {getStatusBadge(action.new_status)}
                    </div>
                  )}

                  {/* Remarks & Descriptions */}
                  {action.remarks && (
                    <div className="mt-2 text-xs text-slate-600 bg-white border border-slate-200 rounded-lg p-2.5">
                      <p className="font-medium text-slate-700 mb-0.5">Procedural Remarks:</p>
                      <p className="whitespace-pre-wrap">{action.remarks}</p>
                    </div>
                  )}

                  {/* Next Step Planning */}
                  {action.next_action_required && (
                    <div className="mt-2 flex items-center gap-2 text-xs bg-amber-50 text-amber-800 border border-amber-200 rounded-md px-2.5 py-1.5">
                      <Clock className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                      <span>
                        <strong>Next Step:</strong> {action.next_action_required}
                        {action.next_action_due_at && (
                          <span className="ml-1 text-amber-700 font-normal">
                            (Due: {new Date(action.next_action_due_at).toLocaleDateString()})
                          </span>
                        )}
                      </span>
                    </div>
                  )}

                  {action.supporting_document_ref && (
                    <div className="mt-2 text-xs text-slate-500">
                      Document Ref: <span className="font-mono text-slate-700">{action.supporting_document_ref}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};
