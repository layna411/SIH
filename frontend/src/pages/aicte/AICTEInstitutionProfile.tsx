import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { InstitutionConsolidatedHistory, AICTECase } from '../../types';
import { api } from '../../services/api';
import { CreateAICTECaseModal } from './CreateAICTECaseModal';
import { ReferGrievanceModal } from './ReferGrievanceModal';
import { 
  Building2, 
  ShieldCheck, 
  CheckCircle2, 
  AlertCircle, 
  ArrowLeft, 
  PlusCircle, 
  ArrowRightLeft, 
  FileText, 
  RefreshCw,
  Clock,
  Layers
} from 'lucide-react';

export const AICTEInstitutionProfile: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<InstitutionConsolidatedHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isIntakeOpen, setIsIntakeOpen] = useState(false);
  const [isReferOpen, setIsReferOpen] = useState(false);

  useEffect(() => {
    if (id) {
      loadProfile();
    }
  }, [id]);

  const loadProfile = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<InstitutionConsolidatedHistory>(`/aicte/institutions/${id}/consolidated-history`);
      setProfile(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load consolidated institution case history.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      RECEIVED: 'bg-slate-100 text-slate-700',
      PENDING_REVIEW: 'bg-amber-50 text-amber-700',
      UNDER_PROCESS: 'bg-blue-50 text-blue-700',
      AWAITING_RESPONSE: 'bg-yellow-50 text-yellow-700',
      TRANSFER_PENDING: 'bg-orange-50 text-orange-700',
      TRANSFERRED: 'bg-orange-100 text-orange-800',
      ESCALATED: 'bg-rose-50 text-rose-700',
      DISPOSED: 'bg-emerald-50 text-emerald-700',
      CLOSED: 'bg-slate-100 text-slate-800',
      REOPENED: 'bg-purple-50 text-purple-700',
    };
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${styles[status] || 'bg-slate-100 text-slate-700'}`}>
        {status.replace('_', ' ')}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="flex items-center gap-3 text-slate-500 text-sm">
          <RefreshCw className="w-5 h-5 animate-spin text-blue-600" />
          Loading consolidated institution profile...
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-center">
          <AlertCircle className="w-8 h-8 text-rose-600 mx-auto mb-2" />
          <h3 className="text-base font-bold text-rose-800 mb-1">Institution Profile Unavailable</h3>
          <p className="text-xs text-rose-600 mb-4">{error || 'Consolidated history could not be retrieved.'}</p>
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 border border-slate-200 bg-white text-slate-700 text-xs rounded-xl hover:bg-slate-50 transition"
          >
            Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Bar Navigation */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="p-2 border border-slate-200 rounded-xl hover:bg-slate-50 text-slate-600 transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900">{profile.name}</h1>
              {profile.is_aicte_verified ? (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  AICTE Verified
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                  Pending AICTE Verification
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Code: <span className="font-mono font-medium text-slate-700">{profile.code}</span>
              {profile.aicte_permanent_id && (
                <span className="ml-3 pl-3 border-l border-slate-200">
                  AICTE PID: <span className="font-mono font-bold text-blue-600">{profile.aicte_permanent_id}</span>
                </span>
              )}
              {profile.region && (
                <span className="ml-3 pl-3 border-l border-slate-200">
                  Region: <strong className="text-slate-700">{profile.region}</strong>
                </span>
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadProfile}
            className="p-2 border border-slate-200 rounded-xl hover:bg-slate-50 text-slate-600 transition text-xs flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
          <button
            onClick={() => setIsReferOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 border border-purple-200 text-purple-700 bg-purple-50 text-xs font-semibold rounded-xl hover:bg-purple-100 transition shadow-sm"
          >
            <ArrowRightLeft className="w-4 h-4" />
            Refer Grievance
          </button>
          <button
            onClick={() => setIsIntakeOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 text-white text-xs font-semibold rounded-xl hover:bg-blue-700 transition shadow-sm"
          >
            <PlusCircle className="w-4 h-4" />
            New AICTE Case
          </button>
        </div>
      </div>

      {/* Aliases Banner if present */}
      {profile.aliases && profile.aliases.length > 0 && (
        <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl text-xs flex items-center gap-2">
          <span className="font-semibold text-slate-600">Official / Historical Aliases:</span>
          <div className="flex flex-wrap gap-1.5">
            {profile.aliases.map((alias, i) => (
              <span key={i} className="px-2 py-0.5 bg-white border border-slate-200 rounded-md text-slate-700 font-medium">
                {alias}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Regulatory Cases</p>
          <p className="text-2xl font-bold text-slate-900 mt-2">{profile.total_cases}</p>
          <p className="text-[11px] text-slate-400 mt-1">Cross-Bureau lifetime docket</p>
        </div>

        <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm">
          <p className="text-xs font-semibold text-amber-600 uppercase tracking-wider">Active Regulatory Cases</p>
          <p className="text-2xl font-bold text-amber-700 mt-2">{profile.active_cases}</p>
          <p className="text-[11px] text-slate-400 mt-1">Under review / inquiry</p>
        </div>

        <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm">
          <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wider">Disposed / Resolved</p>
          <p className="text-2xl font-bold text-emerald-700 mt-2">{profile.disposed_cases}</p>
          <p className="text-[11px] text-slate-400 mt-1">Orders issued / closed</p>
        </div>

        <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm">
          <p className="text-xs font-semibold text-blue-600 uppercase tracking-wider">Bureaus Involved</p>
          <p className="text-2xl font-bold text-blue-700 mt-2">
            {Object.keys(profile.unit_counts || {}).length}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Distinct handling units</p>
        </div>
      </div>

      {/* Handling Bureau Breakdown */}
      {Object.keys(profile.unit_counts || {}).length > 0 && (
        <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm">
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-2">
            <Layers className="w-4 h-4 text-blue-600" />
            Cases by Handling Bureau / Cell
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
            {Object.entries(profile.unit_counts).map(([unit, count]) => (
              <div key={unit} className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-center">
                <span className="font-mono text-xs font-bold text-blue-800">{unit}</span>
                <p className="text-lg font-bold text-slate-800 mt-0.5">{count}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Case Roster */}
      <div className="bg-white border border-slate-200/80 rounded-2xl shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-800">Unified Case Docket</h3>
            <p className="text-xs text-slate-500">Cross-bureau complaint and regulatory case directory for this institution</p>
          </div>
          <span className="text-xs text-slate-400">
            {profile.recent_cases?.length || 0} Case{profile.recent_cases?.length === 1 ? '' : 's'}
          </span>
        </div>

        {(!profile.recent_cases || profile.recent_cases.length === 0) ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            No AICTE regulatory cases recorded for this institution yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Case Reference</th>
                  <th className="py-3 px-4">Handling Bureau</th>
                  <th className="py-3 px-4">Subject & Category</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Last Action</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {profile.recent_cases.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/60 transition">
                    <td className="py-3.5 px-4 font-mono font-bold text-blue-600">
                      <Link to={`/aicte/cases/${c.id}`} className="hover:underline">
                        {c.case_reference}
                      </Link>
                      {c.official_reference_number && (
                        <p className="text-[10px] text-slate-400 font-normal">{c.official_reference_number}</p>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded font-bold bg-blue-50 text-blue-700 border border-blue-200">
                        {c.current_unit_code || 'UNASSIGNED'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 max-w-xs truncate">
                      <p className="font-semibold text-slate-800 truncate">{c.subject}</p>
                      <span className="text-[10px] text-slate-400 uppercase">{c.category}</span>
                    </td>
                    <td className="py-3.5 px-4">
                      {getStatusBadge(c.status)}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500">
                      {new Date(c.last_action_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        to={`/aicte/cases/${c.id}`}
                        className="px-3 py-1.5 bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-700 rounded-lg font-medium transition text-xs"
                      >
                        Open Docket →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Direct Intake Modal */}
      {isIntakeOpen && (
        <CreateAICTECaseModal
          isOpen={isIntakeOpen}
          onClose={() => setIsIntakeOpen(false)}
          onSuccess={() => loadProfile()}
        />
      )}

      {/* Refer Grievance Modal */}
      {isReferOpen && (
        <ReferGrievanceModal
          isOpen={isReferOpen}
          onClose={() => setIsReferOpen(false)}
          onSuccess={() => loadProfile()}
          institutionId={profile.institution_id}
        />
      )}
    </div>
  );
};
