import React, { useState } from 'react';
import { 
  AICTECaseTransfer,
  TransferAcceptPayload, 
  TransferRejectPayload, 
  TransferCancelPayload 
} from '../../types';
import { api } from '../../services/api';
import { X, CheckCircle2, XCircle, AlertCircle, ShieldAlert, Ban } from 'lucide-react';

interface TransferDecisionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  transfer: AICTECaseTransfer;
  actionType: 'ACCEPT' | 'REJECT' | 'CANCEL';
}

export const TransferDecisionModal: React.FC<TransferDecisionModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  transfer,
  actionType,
}) => {
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if ((actionType === 'REJECT' || actionType === 'CANCEL') && !notes.trim()) {
      setError(`Please provide a substantive ${actionType === 'REJECT' ? 'rejection' : 'cancellation'} reason.`);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (actionType === 'ACCEPT') {
        const payload: TransferAcceptPayload = {
          response_notes: notes.trim() || undefined,
        };
        await api.post(`/aicte/transfers/${transfer.id}/accept`, payload);
      } else if (actionType === 'REJECT') {
        const payload: TransferRejectPayload = {
          rejection_reason: notes.trim(),
        };
        await api.post(`/aicte/transfers/${transfer.id}/reject`, payload);
      } else if (actionType === 'CANCEL') {
        const payload: TransferCancelPayload = {
          cancellation_reason: notes.trim(),
        };
        await api.post(`/aicte/transfers/${transfer.id}/cancel`, payload);
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err?.message || `Failed to process transfer ${actionType.toLowerCase()}.`);
    } finally {
      setLoading(false);
    }
  };

  const getModalConfig = () => {
    switch (actionType) {
      case 'ACCEPT':
        return {
          title: 'Accept Case Transfer Handover',
          icon: <CheckCircle2 className="w-5 h-5 text-emerald-600" />,
          btnClass: 'bg-emerald-600 hover:bg-emerald-700 text-white',
          btnText: 'Confirm & Accept Transfer',
          description: `Formally accept case responsibility for ${transfer.case_reference} into ${transfer.to_unit_code}. Case status will transition to TRANSFERRED.`,
          label: 'Acceptance Remarks / Directives (Optional)',
          placeholder: 'Add instructions for the allocated scrutiny officer...',
          required: false,
        };
      case 'REJECT':
        return {
          title: 'Decline Case Transfer Proposal',
          icon: <XCircle className="w-5 h-5 text-rose-600" />,
          btnClass: 'bg-rose-600 hover:bg-rose-700 text-white',
          btnText: 'Decline Transfer Handover',
          description: `Reject transfer proposal. Handling responsibility remains with ${transfer.from_unit_code}, and prior status (${transfer.prior_case_status}) is restored.`,
          label: 'Mandatory Rejection Rationale *',
          placeholder: 'Explain why the case does not fall under your Bureau/Cell jurisdiction...',
          required: true,
        };
      case 'CANCEL':
        return {
          title: 'Withdraw Transfer Proposal',
          icon: <Ban className="w-5 h-5 text-amber-600" />,
          btnClass: 'bg-amber-600 hover:bg-amber-700 text-white',
          btnText: 'Withdraw Proposal',
          description: `Cancel the pending transfer proposal to ${transfer.to_unit_code}. The case will return to prior status (${transfer.prior_case_status}) under ${transfer.from_unit_code}.`,
          label: 'Withdrawal Justification *',
          placeholder: 'Explain why this proposal is being withdrawn...',
          required: true,
        };
    }
  };

  const config = getModalConfig();

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-100">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            {config.icon}
            <h3 className="text-base font-bold text-slate-800">{config.title}</h3>
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
          {/* Transfer Context Box */}
          <div className="p-3.5 bg-slate-50 border border-slate-200/80 rounded-xl space-y-2 text-slate-700">
            <div className="flex items-center justify-between">
              <span className="font-mono font-bold text-blue-600 text-sm">
                {transfer.case_reference}
              </span>
              <span className="px-2 py-0.5 rounded font-mono text-[10px] font-bold bg-slate-200 text-slate-800">
                {transfer.from_unit_code} ➔ {transfer.to_unit_code}
              </span>
            </div>
            <p className="font-medium text-slate-900">{transfer.case_subject}</p>
            <div className="text-[11px] text-slate-600 pt-1 border-t border-slate-200/60">
              <span className="font-semibold text-slate-700">Initiator's Reason:</span> {transfer.transfer_reason}
            </div>
            {transfer.handover_summary && (
              <div className="text-[11px] text-slate-600">
                <span className="font-semibold text-slate-700">Handover Context:</span> {transfer.handover_summary}
              </div>
            )}
          </div>

          <div className="p-3 bg-blue-50/70 border border-blue-200/60 rounded-xl text-slate-700 text-[11px] leading-relaxed">
            {config.description}
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              {config.label}
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder={config.placeholder}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-xs"
              required={config.required}
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
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
              className={`px-5 py-2 rounded-xl font-medium transition shadow-sm ${config.btnClass} disabled:opacity-50`}
            >
              {loading ? 'Processing...' : config.btnText}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
