import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AICTECase, AICTECaseListResponse } from '../../types';
import { api } from '../../services/api';
import { CreateAICTECaseModal } from './CreateAICTECaseModal';
import { ReferGrievanceModal } from './ReferGrievanceModal';
import { 
  ShieldCheck, 
  Layers, 
  Activity, 
  Clock, 
  CheckCircle2, 
  PlusCircle, 
  ArrowRightLeft, 
  Building2, 
  FileText, 
  RefreshCw,
  Search,
  ArrowRight
} from 'lucide-react';

export const AICTEIntegratedDashboard: React.FC = () => {
  const [recentCases, setRecentCases] = useState<AICTECase[]>([]);
  const [totalCases, setTotalCases] = useState(0);
  const [underProcessCount, setUnderProcessCount] = useState(0);
  const [awaitingCount, setAwaitingCount] = useState(0);
  const [disposedCount, setDisposedCount] = useState(0);
  const [pendingOverlapsCount, setPendingOverlapsCount] = useState(0);
  const [unitMetrics, setUnitMetrics] = useState<{ code: string; name: string; count: number }[]>([]);
  const [institutionSearch, setInstitutionSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [isIntakeOpen, setIsIntakeOpen] = useState(false);
  const [isReferOpen, setIsReferOpen] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // 1. Fetch recent cases
      const res = await api.get<AICTECaseListResponse>('/aicte/cases?page=1&page_size=8');
      setRecentCases(res.cases || []);
      setTotalCases(res.total || 0);

      // 2. Fetch status breakdown counts + pending overlaps
      const [underProcRes, awaitingRes, disposedRes, overlapsRes] = await Promise.all([
        api.get<AICTECaseListResponse>('/aicte/cases?status_filter=UNDER_PROCESS&page_size=1'),
        api.get<AICTECaseListResponse>('/aicte/cases?status_filter=AWAITING_RESPONSE&page_size=1'),
        api.get<AICTECaseListResponse>('/aicte/cases?status_filter=DISPOSED&page_size=1'),
        api.get<{ total: number }>('/aicte/overlaps?review_status=PENDING&page_size=1').catch(() => ({ total: 0 })),
      ]);
      setUnderProcessCount(underProcRes.total || 0);
      setAwaitingCount(awaitingRes.total || 0);
      setDisposedCount(disposedRes.total || 0);
      setPendingOverlapsCount(overlapsRes.total || 0);

      // 3. Fetch active units for metrics
      const unitsRes = await api.get<{ units: { id: number; code: string; name: string }[] }>('/aicte/organizational-units');
      const units = unitsRes.units || [];

      // Calculate counts for key bureaus
      const unitPromises = units.slice(0, 6).map(async (u) => {
        try {
          const uRes = await api.get<AICTECaseListResponse>(`/aicte/cases?unit_id=${u.id}&page_size=1`);
          return { code: u.code, name: u.name, count: uRes.total || 0 };
        } catch {
          return { code: u.code, name: u.name, count: 0 };
        }
      });
      const resolvedUnits = await Promise.all(unitPromises);
      setUnitMetrics(resolvedUnits);
    } catch {
      // Keep existing data on error
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

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2.5 rounded-xl bg-blue-600 text-white shadow-md shadow-blue-500/20">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">
                AICTE Integrated Case Monitoring Dashboard
              </h1>
              <p className="text-xs text-slate-500">
                Cross-Bureau Tracking & Unified Institution Oversight (RB, PGRC, Approval Bureau, Regional Offices)
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadDashboardData}
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
            Direct Case Intake
          </button>
        </div>
      </div>

      {/* KPI Overview Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Active Docket</span>
            <Activity className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-3xl font-bold text-slate-900 mt-2">{totalCases}</p>
          <p className="text-[11px] text-slate-400 mt-1">Cross-Bureau complaint cases</p>
        </div>

        <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-blue-600 uppercase tracking-wider">Under Process</span>
            <Clock className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-3xl font-bold text-blue-700 mt-2">{underProcessCount}</p>
          <p className="text-[11px] text-slate-400 mt-1">In active inquiry / committee</p>
        </div>

        <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-600 uppercase tracking-wider">Awaiting Response</span>
            <Layers className="w-4 h-4 text-amber-600" />
          </div>
          <p className="text-3xl font-bold text-amber-700 mt-2">{awaitingCount}</p>
          <p className="text-[11px] text-slate-400 mt-1">Pending college replies</p>
        </div>

        <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider">Disposed Orders</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-3xl font-bold text-emerald-700 mt-2">{disposedCount}</p>
          <p className="text-[11px] text-slate-400 mt-1">Regulatory orders dispatched</p>
        </div>

        <Link
          to="/aicte/overlaps"
          className="p-5 bg-gradient-to-br from-indigo-50/70 to-blue-50/60 border border-blue-200 rounded-2xl shadow-sm hover:shadow transition group block"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-indigo-700 uppercase tracking-wider">Overlap Queue</span>
            <ArrowRightLeft className="w-4 h-4 text-indigo-600 group-hover:translate-x-0.5 transition" />
          </div>
          <p className="text-3xl font-bold text-indigo-900 mt-2">{pendingOverlapsCount}</p>
          <p className="text-[11px] text-indigo-600 font-medium mt-1 flex items-center justify-between">
            <span>Pending review</span>
            <span className="text-[10px] underline">Open Queue →</span>
          </p>
        </Link>
      </div>

      {/* Multi-Bureau Active Distribution Cards */}
      <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
            <Layers className="w-4 h-4 text-blue-600" />
            Cases Distributed Across AICTE Bureaus / Cells
          </h3>
          <Link to="/aicte/cases" className="text-xs text-blue-600 font-semibold hover:underline">
            View All in Directory →
          </Link>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
          {unitMetrics.map((u) => (
            <Link
              key={u.code}
              to={`/aicte/cases?unit_id=${u.code}`}
              className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl hover:bg-blue-50/60 hover:border-blue-200 transition text-center group"
            >
              <span className="font-mono text-xs font-bold text-blue-800 block">{u.code}</span>
              <p className="text-xl font-bold text-slate-800 mt-1 group-hover:text-blue-700">{u.count}</p>
              <span className="text-[10px] text-slate-500 truncate block mt-0.5">{u.name}</span>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Regulatory Cases Stream */}
      <div className="bg-white border border-slate-200/80 rounded-2xl shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-800">Recent Procedural Activity</h3>
            <p className="text-xs text-slate-500">Latest active complaint cases across all handling units</p>
          </div>
          <Link
            to="/aicte/cases"
            className="text-xs text-blue-600 font-semibold hover:underline flex items-center gap-1"
          >
            Full Case Directory <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {recentCases.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            No active AICTE cases found. Use "Direct Case Intake" to register the first regulatory docket.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Case Reference</th>
                  <th className="py-3 px-4">Institution</th>
                  <th className="py-3 px-4">Bureau</th>
                  <th className="py-3 px-4">Subject</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Last Action</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {recentCases.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/60 transition">
                    <td className="py-3 px-4 font-mono font-bold text-blue-600">
                      <Link to={`/aicte/cases/${c.id}`} className="hover:underline">
                        {c.case_reference}
                      </Link>
                    </td>
                    <td className="py-3 px-4 max-w-[200px] truncate">
                      <Link
                        to={`/aicte/institutions/${c.institution_id}`}
                        className="font-semibold text-slate-800 hover:text-blue-600 hover:underline truncate block"
                      >
                        {c.institution_name}
                      </Link>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {c.aicte_permanent_id || c.institution_code}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded font-bold bg-blue-50 text-blue-700 border border-blue-200">
                        {c.current_unit_code || 'UNASSIGNED'}
                      </span>
                    </td>
                    <td className="py-3 px-4 max-w-xs truncate">
                      <p className="font-semibold text-slate-800 truncate">{c.subject}</p>
                      <span className="text-[10px] text-slate-400 uppercase">{c.category}</span>
                    </td>
                    <td className="py-3 px-4">
                      {getStatusBadge(c.status)}
                    </td>
                    <td className="py-3 px-4 text-slate-500">
                      {new Date(c.last_action_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/aicte/cases/${c.id}`}
                        className="px-3 py-1 bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-700 rounded-lg font-medium transition text-xs"
                      >
                        Open →
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
          onSuccess={() => loadDashboardData()}
        />
      )}

      {/* Refer Grievance Modal */}
      {isReferOpen && (
        <ReferGrievanceModal
          isOpen={isReferOpen}
          onClose={() => setIsReferOpen(false)}
          onSuccess={() => loadDashboardData()}
        />
      )}
    </div>
  );
};
