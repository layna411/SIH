import React, { useState, useEffect } from 'react';
import { CreateAICTECasePayload, AICTEComplainantType, GrievancePriority } from '../../types';
import { api } from '../../services/api';
import { X, PlusCircle, AlertCircle, Building2, ShieldCheck } from 'lucide-react';

interface CreateAICTECaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (newCase: any) => void;
}

interface UnitOption {
  id: number;
  name: string;
  code: string;
  unit_type: string;
}

interface InstitutionOption {
  id: number;
  name: string;
  code: string;
  aicte_permanent_id?: string;
  region?: string;
}

const COMPLAINANT_TYPES: { value: AICTEComplainantType; label: string }[] = [
  { value: 'STUDENT', label: 'Student / Enrolled Scholar' },
  { value: 'FACULTY', label: 'Faculty / Academic Staff' },
  { value: 'STAKEHOLDER', label: 'Parent / Citizen / Stakeholder' },
  { value: 'INSTITUTION', label: 'Institution / Management Authority' },
  { value: 'PUBLIC_AUTHORITY', label: 'Ministry / Directorate / State Authority' },
  { value: 'ANONYMOUS', label: 'Anonymous Whistleblower' },
  { value: 'OTHER', label: 'Other Third Party' },
];

const CATEGORIES = [
  'APPROVAL_VIOLATION',
  'FACULTY_NORMS',
  'CAPITATION_FEE',
  'STUDENT_GRIEVANCE',
  'INFRASTRUCTURE_DEFICIT',
  'LAND_DEFICIT',
  'REGULATION_AUDIT',
  'ACCREDITATION_ISSUE',
  'FINANCIAL_MALPRACTICE',
  'OTHER',
];

export const CreateAICTECaseModal: React.FC<CreateAICTECaseModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [units, setUnits] = useState<UnitOption[]>([]);
  const [institutions, setInstitutions] = useState<InstitutionOption[]>([]);
  const [selectedInstId, setSelectedInstId] = useState<number | ''>('');
  const [selectedUnitId, setSelectedUnitId] = useState<number | ''>('');
  const [category, setCategory] = useState('APPROVAL_VIOLATION');
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [complainantType, setComplainantType] = useState<AICTEComplainantType>('STAKEHOLDER');
  const [officialRef, setOfficialRef] = useState('');
  const [priority, setPriority] = useState<GrievancePriority>('NORMAL');
  const [region, setRegion] = useState('');
  const [nextActionRequired, setNextActionRequired] = useState('');
  const [loading, setLoading] = useState(false);
  const [fetchingOptions, setFetchingOptions] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadPrerequisites();
    }
  }, [isOpen]);

  const loadPrerequisites = async () => {
    setFetchingOptions(true);
    setError(null);
    try {
      // Fetch active units
      const unitsRes = await api.get<{ units: UnitOption[] }>('/aicte/organizational-units');
      setUnits(unitsRes.units || []);
      if (unitsRes.units && unitsRes.units.length > 0) {
        setSelectedUnitId(unitsRes.units[0].id);
      }

      // Fetch institutions directory
      const instRes = await api.get<{ items: InstitutionOption[] }>('/institutions?page_size=100');
      setInstitutions(instRes.items || []);
      if (instRes.items && instRes.items.length > 0) {
        setSelectedInstId(instRes.items[0].id);
        setRegion(instRes.items[0].region || '');
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load organizational units or institutions.');
    } finally {
      setFetchingOptions(false);
    }
  };

  const handleInstitutionChange = (id: number) => {
    setSelectedInstId(id);
    const inst = institutions.find(i => i.id === id);
    if (inst && inst.region) {
      setRegion(inst.region);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInstId || !selectedUnitId || !subject.trim() || !description.trim()) {
      setError('Please fill in all mandatory fields.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload: CreateAICTECasePayload = {
        institution_id: Number(selectedInstId),
        current_unit_id: Number(selectedUnitId),
        category,
        subject: subject.trim(),
        description: description.trim(),
        complainant_type: complainantType,
        official_reference_number: officialRef.trim() || undefined,
        priority,
        region: region.trim() || undefined,
        next_action_required: nextActionRequired.trim() || undefined,
      };

      const result = await api.post('/aicte/cases', payload);
      onSuccess(result);
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to create AICTE case.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-slate-100 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-blue-50 text-blue-600">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-800">Direct AICTE Case Intake</h3>
              <p className="text-xs text-slate-500">Official Regulatory Incident / Inspection Intake</p>
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

        {fetchingOptions ? (
          <div className="py-12 text-center text-slate-500 text-xs">
            Loading institutions and AICTE units...
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-4 space-y-4 text-xs">
            {/* Institution & Handling Bureau */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Target Institution <span className="text-rose-500">*</span>
                </label>
                <select
                  value={selectedInstId}
                  onChange={(e) => handleInstitutionChange(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  required
                >
                  <option value="">-- Select Verified Institution --</option>
                  {institutions.map(inst => (
                    <option key={inst.id} value={inst.id}>
                      {inst.name} ({inst.code}{inst.aicte_permanent_id ? ` | ${inst.aicte_permanent_id}` : ''})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Responsible Bureau / Cell <span className="text-rose-500">*</span>
                </label>
                <select
                  value={selectedUnitId}
                  onChange={(e) => setSelectedUnitId(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  required
                >
                  <option value="">-- Select Responsible Bureau --</option>
                  {units.map(unit => (
                    <option key={unit.id} value={unit.id}>
                      [{unit.code}] {unit.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Subject */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Concise Case Subject / Allegation <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="e.g. Discrepancy in sanctioned faculty strength during annual approval audit"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                required
              />
            </div>

            {/* Category & Complainant Type */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Regulatory Category <span className="text-rose-500">*</span>
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                >
                  {CATEGORIES.map(cat => (
                    <option key={cat} value={cat}>{cat.replace(/_/g, ' ')}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Complainant / Source Type <span className="text-rose-500">*</span>
                </label>
                <select
                  value={complainantType}
                  onChange={(e) => setComplainantType(e.target.value as AICTEComplainantType)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                >
                  {COMPLAINANT_TYPES.map(ct => (
                    <option key={ct.value} value={ct.value}>{ct.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Official Ref, Priority & Region */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Official / External Ref No.
                </label>
                <input
                  type="text"
                  value={officialRef}
                  onChange={(e) => setOfficialRef(e.target.value)}
                  placeholder="e.g. AICTE/RO-W/2026/890"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Priority</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as GrievancePriority)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                >
                  <option value="LOW">Low</option>
                  <option value="NORMAL">Normal</option>
                  <option value="HIGH">High</option>
                  <option value="URGENT">Urgent / Critical</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Region</label>
                <input
                  type="text"
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                  placeholder="e.g. Northern / Western"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Protected Regulatory Description <span className="text-rose-500">*</span>
              </label>
              <textarea
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Comprehensive narrative of the regulatory complaint, inspection findings, or statutory query..."
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                required
              />
            </div>

            {/* Next Action Planning */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Initial Next Action Required
              </label>
              <input
                type="text"
                value={nextActionRequired}
                onChange={(e) => setNextActionRequired(e.target.value)}
                placeholder="e.g. Issue scrutiny notice to institution within 7 days"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
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
                <PlusCircle className="w-4 h-4" />
                {loading ? 'Registering...' : 'Register AICTE Case'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
