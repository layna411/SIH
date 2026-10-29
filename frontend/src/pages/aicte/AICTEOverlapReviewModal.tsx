import React, { useState } from 'react';
import { AICTEOverlapReviewStatus, OverlapReviewPayload } from '../../types';
import { X, CheckCircle, ShieldAlert, AlertCircle, Send, ArrowRightLeft, Clock } from 'lucide-react';

interface AICTEOverlapReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: OverlapReviewPayload) => Promise<void>;
  overlapId: number;
  caseLowRef: string;
  caseHighRef: string;
  currentDecision?: AICTEOverlapReviewStatus;
}

const DECISIONS: {
  value: AICTEOverlapReviewStatus;
  label: string;
  description: string;
  badgeClass: string;
}[] = [
  {
    value: 'CONFIRMED_DUPLICATE',
    label: 'Confirm Duplicate Case',
    description: 'Cases concern the same underlying statutory allegation. Creates a DUPLICATE_OF administrative link while keeping official dockets independent.',
    badgeClass: 'bg-rose-50 border-rose-200 text-rose-800',
  },
  {
    value: 'CONFIRMED_RELATED',
    label: 'Confirm Related Case',
    description: 'Cases concern the same institution with related issues but require separate bureau proceedings. Creates a RELATED_TO link.',
    badgeClass: 'bg-blue-50 border-blue-200 text-blue-800',
  },
  {
    value: 'REJECTED',
    label: 'Reject Overlap Match',
    description: 'Cases are independent or false match. Deactivates any link. Official case statuses remain unchanged.',
    badgeClass: 'bg-slate-50 border-slate-200 text-slate-800',
  },
  {
    value: 'DEFERRED',
    label: 'Defer Review Decision',
    description: 'Awaiting further committee scrutiny, explanation letters, or inspection findings before deciding.',
    badgeClass: 'bg-amber-50 border-amber-200 text-amber-800',
  },
];

export const AICTEOverlapReviewModal: React.FC<AICTEOverlapReviewModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  overlapId,
  caseLowRef,
  caseHighRef,
  currentDecision = 'PENDING',
}) => {
  const [selectedDecision, setSelectedDecision] = useState<AICTEOverlapReviewStatus>('CONFIRMED_DUPLICATE');
  const [reviewNotes, setReviewNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reviewNotes.trim()) {
      setError('Please provide a substantive justification note for this review decision.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await onSubmit({
        action: selectedDecision,
        review_notes: reviewNotes.trim(),
      });
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to submit review decision.');
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
              <CheckCircle className="w-5 h-5 text-blue-600" />
              Human Review Decision
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Candidate Overlap: <span className="font-mono font-semibold text-blue-600">{caseLowRef}</span> ➔ <span className="font-mono font-semibold text-blue-600">{caseHighRef}</span>
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
          {/* Statutory Safeguard Notice */}
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 flex items-start gap-2.5">
            <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div className="text-[11px] leading-relaxed">
              <strong>Administrative Independence Principle:</strong> Review decisions establish an administrative relationship between cases. Official case dockets, references, and statuses are <em>never automatically merged or closed</em>.
            </div>
          </div>

          {/* Decision Options */}
          <div>
            <label className="block font-semibold text-slate-700 mb-2">
              Select Review Determination <span className="text-rose-500">*</span>
            </label>
            <div className="space-y-2">
              {DECISIONS.map((opt) => (
                <label
                  key={opt.value}
                  className={`block p-3 rounded-xl border cursor-pointer transition ${
                    selectedDecision === opt.value
                      ? `${opt.badgeClass} ring-2 ring-blue-500 shadow-sm`
                      : 'border-slate-200 bg-slate-50/50 hover:bg-slate-100/60'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <input
                      type="radio"
                      name="decision"
                      value={opt.value}
                      checked={selectedDecision === opt.value}
                      onChange={() => setSelectedDecision(opt.value)}
                      className="mt-0.5 text-blue-600 focus:ring-blue-500"
                    />
                    <div>
                      <p className="font-bold text-xs">{opt.label}</p>
                      <p className="text-[11px] text-slate-500 mt-0.5 leading-normal">{opt.description}</p>
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Justification Notes */}
          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Statutory Justification & Review Notes <span className="text-rose-500">*</span>
            </label>
            <textarea
              rows={4}
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              placeholder="Provide explainable reasons, committee observations, or coordination directions for this determination..."
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-xs"
              required
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
              {loading ? 'Submitting...' : 'Record Review Determination'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
