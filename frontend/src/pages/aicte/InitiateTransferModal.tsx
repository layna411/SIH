import React, { useState, useEffect } from 'react';
import { TransferInitiatePayload } from '../../types';
import { api } from '../../services/api';
import { X, ArrowRightLeft, ShieldAlert, AlertCircle, Send } from 'lucide-react';

interface InitiateTransferModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  caseId: number;
  caseReference: string;
  currentUnitId: number;
  currentUnitCode?: string;
}

interface UnitOption {
  id: number;
  code: string;
  name: string;
  unit_type: string;
}

export const InitiateTransferModal: React.FC<InitiateTransferModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  caseId,
  caseReference,
  currentUnitId,
  currentUnitCode,
}) => {
  const [units, setUnits] = useState<UnitOption[]>([]);
  const [selectedUnitId, setSelectedUnitId] = useState<string>('');
  const [transferReason, setTransferReason] = useState('');
  const [handoverSummary, setHandoverSummary] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadUnits();
    }
  }, [isOpen]);

  const loadUnits = async () => {
    try {
      const res = await api.get<{ units: UnitOption[] }>('/aicte/organizational-units');
      // Filter out the current unit
      const eligible = (res.units || []).filter((u) => u.id !== currentUnitId);
      setUnits(eligible);
      if (eligible.length > 0) {
        setSelectedUnitId(eligible[0].id.toString());
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load organizational units.');
    }
  };

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUnitId) {
      setError('Please select a destination organizational unit.');
      return;
    }
    if (transferReason.trim().length < 10) {
      setError('Please provide a substantive transfer reason (at least 10 characters).');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const payload: TransferInitiatePayload = {
        to_unit_id: parseInt(selectedUnitId, 10),
        transfer_reason: transferReason.trim(),
        handover_summary: handoverSummary.trim() || undefined,
      };
      await api.post(`/aicte/cases/${caseId}/transfers`, payload);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to initiate case transfer.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-100 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div>
            <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
              <ArrowRightLeft className="w-5 h-5 text-blue-600" />
              Initiate Inter-Bureau Case Transfer
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Case Docket: <span className="font-mono font-semibold text-blue-600">{caseReference}</span> | Originating Unit: <span className="font-bold text-slate-700">{currentUnitCode || `#${currentUnitId}`}</span>
            </p>
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
          {/* Statutory Handover Safeguard Warning */}
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-blue-900 flex items-start gap-2.5">
            <ShieldAlert className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <div className="text-[11px] leading-relaxed">
              <strong>Controlled Handover Principle:</strong> Initiating a transfer moves the case to <code className="font-mono bg-blue-100 px-1 py-0.2 rounded">TRANSFER_PENDING</code>. Handling responsibility and assigned officer remain with the originating bureau until the receiving bureau formally accepts the case.
            </div>
          </div>

          {/* Destination Unit Selector */}
          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Destination Bureau / Cell <span className="text-rose-500">*</span>
            </label>
            <select
              value={selectedUnitId}
              onChange={(e) => setSelectedUnitId(e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-xs bg-white"
              required
            >
              {units.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.code} — {u.name} ({u.unit_type})
                </option>
              ))}
            </select>
          </div>

          {/* Transfer Reason */}
          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Formal Transfer Reason & Statutory Justification <span className="text-rose-500">*</span>
            </label>
            <textarea
              rows={3}
              value={transferReason}
              onChange={(e) => setTransferReason(e.target.value)}
              placeholder="Explain the jurisdictional mandate, category mismatch, or formal referral rationale for this transfer..."
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-xs"
              required
            />
          </div>

          {/* Handover Summary */}
          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Executive Handover Summary & Pending Steps (Optional)
            </label>
            <textarea
              rows={3}
              value={handoverSummary}
              onChange={(e) => setHandoverSummary(e.target.value)}
              placeholder="Outline inquiry milestones completed to date, documentary evidence secured, and immediate procedural actions required..."
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-xs"
            />
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
              {loading ? 'Submitting...' : 'Submit Transfer Proposal'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
