import React, { useState, useEffect } from 'react';
import { ReferGrievancePayload, AICTEComplainantType, GrievancePriority } from '../../types';
import { api } from '../../services/api';
import { X, ArrowRightLeft, AlertCircle, ShieldAlert } from 'lucide-react';

interface ReferGrievanceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (referredCase: any) => void;
  grievanceId?: number;
  grievanceRef?: string;
  institutionId?: number;
}

interface UnitOption {
  id: number;
  name: string;
  code: string;
  unit_type: string;
}

export const ReferGrievanceModal: React.FC<ReferGrievanceModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  grievanceId,
  grievanceRef,
}) => {
  const [sourceId, setSourceId] = useState<number | ''>(grievanceId || '');
  const [units, setUnits] = useState<UnitOption[]>([]);
  const [selectedUnitId, setSelectedUnitId] = useState<number | ''>('');
  const [referralReason, setReferralReason] = useState('');
  const [complainantType, setComplainantType] = useState<AICTEComplainantType>('STUDENT');
  const [priority, setPriority] = useState<GrievancePriority>('HIGH');
  const [officialRef, setOfficialRef] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      if (grievanceId) setSourceId(grievanceId);
      loadUnits();
    }
  }, [isOpen, grievanceId]);

  const loadUnits = async () => {
    try {
      const res = await api.get<{ units: UnitOption[] }>('/aicte/organizational-units');
      setUnits(res.units || []);
      const pgrc = res.units?.find(u => u.code === 'PGRC');
      if (pgrc) {
        setSelectedUnitId(pgrc.id);
      } else if (res.units && res.units.length > 0) {
        setSelectedUnitId(res.units[0].id);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load organizational units.');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceId || !selectedUnitId || !referralReason.trim()) {
      setError('Please provide the grievance ID, receiving Bureau, and justification.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload: ReferGrievancePayload = {
        source_grievance_id: Number(sourceId),
        destination_unit_id: Number(selectedUnitId),
        referral_reason: referralReason.trim(),
        complainant_type: complainantType,
        priority,
        official_reference_number: officialRef.trim() || undefined,
      };

      const result = await api.post('/aicte/cases/refer-grievance', payload);
      onSuccess(result);
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to refer grievance to AICTE case.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-100">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-purple-50 text-purple-600">
              <ArrowRightLeft className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-800">Refer Campus Grievance to AICTE</h3>
              <p className="text-xs text-slate-500">
                {grievanceRef ? `Grievance Reference: ${grievanceRef}` : 'Formal Bureau Regulatory Referral'}
              </p>
            </div>
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
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-800">
            <p className="font-semibold mb-1 flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4 text-amber-600" />
              Statutory Referral Notice
            </p>
            <p className="text-[11px] leading-relaxed">
              Referring a campus grievance creates an official AICTE regulatory case. The original grievance history remains intact and will be linked to the new AICTE docket.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Source Grievance ID <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                value={sourceId}
                onChange={(e) => setSourceId(Number(e.target.value))}
                placeholder="e.g. 1024"
                disabled={Boolean(grievanceId)}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none disabled:bg-slate-50"
                required
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Receiving AICTE Bureau / Cell <span className="text-rose-500">*</span>
              </label>
              <select
                value={selectedUnitId}
                onChange={(e) => setSelectedUnitId(Number(e.target.value))}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                required
              >
                <option value="">-- Select Receiving Bureau --</option>
                {units.map(unit => (
                  <option key={unit.id} value={unit.id}>
                    [{unit.code}] {unit.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Statutory Justification for Referral <span className="text-rose-500">*</span>
            </label>
            <textarea
              rows={3}
              value={referralReason}
              onChange={(e) => setReferralReason(e.target.value)}
              placeholder="State the non-compliance, statutory violation, or reason why internal campus resolution failed..."
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as GrievancePriority)}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              >
                <option value="NORMAL">Normal</option>
                <option value="HIGH">High</option>
                <option value="URGENT">Urgent / Critical</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                External / Official Ref No. (Optional)
              </label>
              <input
                type="text"
                value={officialRef}
                onChange={(e) => setOfficialRef(e.target.value)}
                placeholder="e.g. AICTE/PGRC/REF/2026/01"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              />
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
              className="flex items-center gap-2 px-5 py-2 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-700 disabled:opacity-50 transition shadow-sm"
            >
              <ArrowRightLeft className="w-4 h-4" />
              {loading ? 'Submitting Referral...' : 'Initiate AICTE Referral'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
