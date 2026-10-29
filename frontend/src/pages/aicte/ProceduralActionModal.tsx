import React, { useState } from 'react';
import { 
  AICTECaseActionType, 
  AICTECaseStatus, 
  AddCaseActionPayload 
} from '../../types';
import { X, Send, AlertCircle } from 'lucide-react';

interface ProceduralActionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: AddCaseActionPayload) => Promise<void>;
  currentStatus: AICTECaseStatus;
  caseReference: string;
}

const ACTION_TYPES: { value: AICTECaseActionType; label: string }[] = [
  { value: 'INITIAL_SCRUTINY', label: 'Initial Scrutiny & Document Check' },
  { value: 'INFO_REQUESTED', label: 'Clarification / Information Requested' },
  { value: 'EXPLANATION_RECEIVED', label: 'Explanation / Response Received' },
  { value: 'COMMITTEE_REVIEW', label: 'Hearing / Standing Committee Review' },
  { value: 'HEARING_SCHEDULED', label: 'Formal Hearing Scheduled' },
  { value: 'HEARING_COMPLETED', label: 'Hearing Completed' },
  { value: 'COMPLIANCE_VERIFIED', label: 'Compliance Verification Completed' },
  { value: 'TRANSFER_INITIATED', label: 'Initiate Transfer to another Bureau/Cell' },
  { value: 'ESCALATION', label: 'Escalate Case to Higher Authority' },
  { value: 'DISPOSAL_ORDER', label: 'Issue Disposal / Regulatory Order' },
  { value: 'STATUS_UPDATE', label: 'General Status / Progress Update' },
  { value: 'NOTE_RECORDED', label: 'Procedural Case Note Recorded' },
];

const STATUS_OPTIONS: { value: AICTECaseStatus; label: string }[] = [
  { value: 'PENDING_REVIEW', label: 'Pending Review' },
  { value: 'UNDER_PROCESS', label: 'Under Process' },
  { value: 'AWAITING_RESPONSE', label: 'Awaiting Response from College/Complainant' },
  { value: 'TRANSFER_PENDING', label: 'Transfer Pending' },
  { value: 'ESCALATED', label: 'Escalated' },
  { value: 'DISPOSED', label: 'Disposed (Regulatory Order Issued)' },
  { value: 'CLOSED', label: 'Closed' },
  { value: 'REOPENED', label: 'Reopened' },
];

export const ProceduralActionModal: React.FC<ProceduralActionModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  currentStatus,
  caseReference,
}) => {
  const [actionType, setActionType] = useState<AICTECaseActionType>('INITIAL_SCRUTINY');
  const [actionTitle, setActionTitle] = useState('');
  const [actionDescription, setActionDescription] = useState('');
  const [newStatus, setNewStatus] = useState<AICTECaseStatus | ''>('');
  const [remarks, setRemarks] = useState('');
  const [supportingDocRef, setSupportingDocRef] = useState('');
  const [nextActionRequired, setNextActionRequired] = useState('');
  const [nextActionDueDate, setNextActionDueDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!actionTitle.trim()) {
      setError('Action title is required.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload: AddCaseActionPayload = {
        action_type: actionType,
        action_title: actionTitle.trim(),
        action_description: actionDescription.trim() || undefined,
        new_status: (newStatus || undefined) as AICTECaseStatus | undefined,
        remarks: remarks.trim() || undefined,
        supporting_document_ref: supportingDocRef.trim() || undefined,
        next_action_required: nextActionRequired.trim() || undefined,
        next_action_due_at: nextActionDueDate ? new Date(nextActionDueDate).toISOString() : undefined,
      };

      await onSubmit(payload);
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to record procedural action.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-slate-100">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div>
            <h3 className="text-lg font-bold text-slate-800">Record Procedural Action</h3>
            <p className="text-xs text-slate-500">Case Reference: <span className="font-mono text-blue-600 font-semibold">{caseReference}</span></p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-4 text-xs">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Action Type <span className="text-rose-500">*</span>
              </label>
              <select
                value={actionType}
                onChange={(e) => {
                  const val = e.target.value as AICTECaseActionType;
                  setActionType(val);
                  if (!actionTitle) {
                    const match = ACTION_TYPES.find(a => a.value === val);
                    if (match) setActionTitle(match.label);
                  }
                }}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              >
                {ACTION_TYPES.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Action Title <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                value={actionTitle}
                onChange={(e) => setActionTitle(e.target.value)}
                placeholder="e.g. Explanation letter served to Principal"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Update Case Status (Current: <span className="text-blue-600">{currentStatus}</span>)
              </label>
              <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value as AICTECaseStatus | '')}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              >
                <option value="">-- Retain Current Status ({currentStatus}) --</option>
                {STATUS_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Supporting Document / Dispatch Ref
              </label>
              <input
                type="text"
                value={supportingDocRef}
                onChange={(e) => setSupportingDocRef(e.target.value)}
                placeholder="e.g. AICTE/RB/DISP/2026/104"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Remarks & Detailed Regulatory Findings
            </label>
            <textarea
              rows={3}
              value={remarks}
              onChange={(e) => setRemarks(e.target.value)}
              placeholder="Enter official observations, hearing minutes, or specific directions issued..."
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl space-y-3">
            <p className="font-semibold text-slate-700 text-xs">Next Action Planning (Milestone Tracking)</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-600 mb-1">Next Action Required</label>
                <input
                  type="text"
                  value={nextActionRequired}
                  onChange={(e) => setNextActionRequired(e.target.value)}
                  placeholder="e.g. Verify compliance submission"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-600 mb-1">Next Action Due Date</label>
                <input
                  type="date"
                  value={nextActionDueDate}
                  onChange={(e) => setNextActionDueDate(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 border border-slate-200 text-slate-600 rounded-xl hover:bg-slate-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 transition shadow-sm"
            >
              <Send className="w-4 h-4" />
              {loading ? 'Recording...' : 'Commit Procedural Action'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
