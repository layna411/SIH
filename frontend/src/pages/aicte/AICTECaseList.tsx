import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AICTECase, AICTECaseListResponse, AICTECaseStatus } from '../../types';
import { api } from '../../services/api';
import { CreateAICTECaseModal } from './CreateAICTECaseModal';
import { 
  Search, 
  Filter, 
  PlusCircle, 
  RefreshCw, 
  Building2, 
  ShieldCheck, 
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  ArrowRight
} from 'lucide-react';

interface UnitOption {
  id: number;
  name: string;
  code: string;
}

export const AICTECaseList: React.FC = () => {
  const [cases, setCases] = useState<AICTECase[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [unitFilter, setUnitFilter] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const [units, setUnits] = useState<UnitOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isIntakeOpen, setIsIntakeOpen] = useState(false);

  useEffect(() => {
    loadUnits();
  }, []);

  useEffect(() => {
    loadCases();
  }, [page, statusFilter, unitFilter, priorityFilter]);

  const loadUnits = async () => {
    try {
      const res = await api.get<{ units: UnitOption[] }>('/aicte/organizational-units');
      setUnits(res.units || []);
    } catch {
      // Ignore background unit load error
    }
  };

  const loadCases = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.append('page', page.toString());
      params.append('page_size', pageSize.toString());
      if (search.trim()) params.append('search', search.trim());
      if (statusFilter) params.append('status_filter', statusFilter);
      if (unitFilter) params.append('unit_id', unitFilter);
      if (priorityFilter) params.append('priority', priorityFilter);

      const res = await api.get<AICTECaseListResponse>(`/aicte/cases?${params.toString()}`);
      setCases(res.cases || []);
      setTotal(res.total || 0);
    } catch (err: any) {
      setError(err?.message || 'Failed to load AICTE cases.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadCases();
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

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-blue-600" />
            AICTE Case Directory
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Cross-Bureau Case Tracking across RB, PGRC, Approval Bureau, and Regional Offices
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => loadCases()}
            className="p-2 border border-slate-200 rounded-xl hover:bg-slate-50 text-slate-600 transition text-xs flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
          <button
            onClick={() => setIsIntakeOpen(true)}
            className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-xs font-semibold rounded-xl hover:bg-blue-700 transition shadow-sm"
          >
            <PlusCircle className="w-4 h-4" />
            New AICTE Case Intake
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 bg-white border border-slate-200/80 rounded-2xl shadow-sm space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by Case Ref, Subject, Category, Institution Name or AICTE Permanent ID..."
              className="w-full pl-10 pr-4 py-2 text-xs border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-slate-900 text-white text-xs font-semibold rounded-xl hover:bg-slate-800 transition"
          >
            Search
          </button>
        </form>

        <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-100 text-xs">
          <div className="flex items-center gap-1.5 text-slate-500">
            <Filter className="w-3.5 h-3.5" />
            <span className="font-semibold">Filters:</span>
          </div>

          {/* Bureau Filter */}
          <select
            value={unitFilter}
            onChange={(e) => { setUnitFilter(e.target.value); setPage(1); }}
            className="px-2.5 py-1.5 border border-slate-200 rounded-lg text-slate-700 outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All Bureaus / Units</option>
            {units.map(u => (
              <option key={u.id} value={u.id}>[{u.code}] {u.name}</option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="px-2.5 py-1.5 border border-slate-200 rounded-lg text-slate-700 outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="RECEIVED">Received</option>
            <option value="PENDING_REVIEW">Pending Review</option>
            <option value="UNDER_PROCESS">Under Process</option>
            <option value="AWAITING_RESPONSE">Awaiting Response</option>
            <option value="TRANSFER_PENDING">Transfer Pending</option>
            <option value="TRANSFERRED">Transferred</option>
            <option value="ESCALATED">Escalated</option>
            <option value="DISPOSED">Disposed</option>
            <option value="CLOSED">Closed</option>
            <option value="REOPENED">Reopened</option>
          </select>

          {/* Priority Filter */}
          <select
            value={priorityFilter}
            onChange={(e) => { setPriorityFilter(e.target.value); setPage(1); }}
            className="px-2.5 py-1.5 border border-slate-200 rounded-lg text-slate-700 outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All Priorities</option>
            <option value="LOW">Low</option>
            <option value="NORMAL">Normal</option>
            <option value="HIGH">High</option>
            <option value="URGENT">Urgent</option>
          </select>

          {(search || statusFilter || unitFilter || priorityFilter) && (
            <button
              onClick={() => {
                setSearch('');
                setStatusFilter('');
                setUnitFilter('');
                setPriorityFilter('');
                setPage(1);
              }}
              className="text-blue-600 hover:underline font-semibold ml-auto"
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Case Table Container */}
      <div className="bg-white border border-slate-200/80 rounded-2xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500 text-xs flex items-center justify-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
            Loading cases...
          </div>
        ) : error ? (
          <div className="p-8 text-center text-rose-600 text-xs">
            <AlertCircle className="w-6 h-6 mx-auto mb-1 text-rose-500" />
            {error}
          </div>
        ) : cases.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            No AICTE cases match the specified search or filter criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Case Reference</th>
                  <th className="py-3 px-4">Institution</th>
                  <th className="py-3 px-4">Handling Bureau</th>
                  <th className="py-3 px-4">Subject & Allegation</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Last Action</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {cases.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/60 transition">
                    <td className="py-3 px-4 font-mono font-bold text-blue-600">
                      <Link to={`/aicte/cases/${c.id}`} className="hover:underline">
                        {c.case_reference}
                      </Link>
                      {c.official_reference_number && (
                        <p className="text-[10px] text-slate-400 font-normal">{c.official_reference_number}</p>
                      )}
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
                        className="inline-flex items-center gap-1 px-3 py-1 bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-700 rounded-lg font-medium transition text-xs"
                      >
                        View <ArrowRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <span>
            Showing {cases.length} of {total} case{total === 1 ? '' : 's'}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="p-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 transition"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="p-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 transition"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Direct Intake Modal */}
      {isIntakeOpen && (
        <CreateAICTECaseModal
          isOpen={isIntakeOpen}
          onClose={() => setIsIntakeOpen(false)}
          onSuccess={() => { setPage(1); loadCases(); }}
        />
      )}
    </div>
  );
};
