import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AICTECaseTransfer, AICTETransferStatus } from '../../types';
import { api } from '../../services/api';
import { TransferDecisionModal } from './TransferDecisionModal';
import { 
  ArrowRightLeft, 
  Inbox, 
  Send, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  ChevronLeft, 
  ChevronRight,
  Search,
  Filter,
  Check,
  X,
  Ban
} from 'lucide-react';

export const AICTETransferQueue: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'INCOMING' | 'OUTGOING'>('INCOMING');
  const [transfers, setTransfers] = useState<AICTECaseTransfer[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [statusFilter, setStatusFilter] = useState<string>('PENDING_ACCEPTANCE');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Decision Modal State
  const [selectedTransfer, setSelectedTransfer] = useState<AICTECaseTransfer | null>(null);
  const [decisionAction, setDecisionAction] = useState<'ACCEPT' | 'REJECT' | 'CANCEL' | null>(null);

  useEffect(() => {
    loadTransfers();
  }, [activeTab, page, statusFilter]);

  const loadTransfers = async () => {
    setLoading(true);
    setError(null);
    try {
      const endpoint = activeTab === 'INCOMING' 
        ? '/aicte/transfers/incoming' 
        : '/aicte/transfers/outgoing';

      const params = new URLSearchParams();
      params.append('page', page.toString());
      params.append('page_size', pageSize.toString());
      if (statusFilter) params.append('status', statusFilter);

      const res = await api.get<{
        items: AICTECaseTransfer[];
        total: number;
        page: number;
        page_size: number;
      }>(`${endpoint}?${params.toString()}`);

      setTransfers(res.items || []);
      setTotal(res.total || 0);
    } catch (err: any) {
      setError(err?.message || 'Failed to load transfer queue.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: AICTETransferStatus) => {
    const map: Record<AICTETransferStatus, { label: string; cls: string }> = {
      PENDING_ACCEPTANCE: { label: 'Pending Acceptance', cls: 'bg-amber-50 text-amber-700 border-amber-200' },
      ACCEPTED: { label: 'Accepted Handover', cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
      REJECTED: { label: 'Declined', cls: 'bg-rose-50 text-rose-700 border-rose-200' },
      CANCELLED: { label: 'Withdrawn', cls: 'bg-slate-100 text-slate-700 border-slate-200' },
    };
    const s = map[status] || { label: status, cls: 'bg-slate-100 text-slate-700' };
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${s.cls}`}>
        {s.label}
      </span>
    );
  };

  const filteredTransfers = transfers.filter((t) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      t.case_reference.toLowerCase().includes(q) ||
      t.institution_name.toLowerCase().includes(q) ||
      (t.institution_aicte_pid && t.institution_aicte_pid.toLowerCase().includes(q)) ||
      t.case_subject.toLowerCase().includes(q)
    );
  });

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ArrowRightLeft className="w-6 h-6 text-blue-600" />
            <h1 className="text-xl font-bold text-slate-900">
              Inter-Bureau Case Transfer Queue
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Formal, auditable responsibility handover across AICTE Bureaus, Cells, and Regional Offices.
          </p>
        </div>

        <button
          onClick={loadTransfers}
          className="flex items-center gap-1.5 px-3 py-1.5 border border-slate-200 rounded-xl text-xs font-medium text-slate-600 hover:bg-slate-50 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Queue
        </button>
      </div>

      {/* Main Tabs (Incoming vs Outgoing) */}
      <div className="flex items-center gap-3 border-b border-slate-200">
        <button
          onClick={() => {
            setActiveTab('INCOMING');
            setPage(1);
          }}
          className={`flex items-center gap-2 pb-3 px-2 text-sm font-semibold transition border-b-2 ${
            activeTab === 'INCOMING'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Inbox className="w-4 h-4" />
          Incoming Proposals (Awaiting Our Review)
        </button>

        <button
          onClick={() => {
            setActiveTab('OUTGOING');
            setPage(1);
          }}
          className={`flex items-center gap-2 pb-3 px-2 text-sm font-semibold transition border-b-2 ${
            activeTab === 'OUTGOING'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Send className="w-4 h-4" />
          Outgoing Proposals (Sent by Our Bureau)
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 bg-white border border-slate-200/80 rounded-2xl shadow-sm space-y-3 text-xs">
        {/* Status Pills */}
        <div className="flex flex-wrap items-center gap-2 pb-2 border-b border-slate-100">
          {[
            { id: 'PENDING_ACCEPTANCE', label: 'Pending Acceptance' },
            { id: 'ACCEPTED', label: 'Accepted' },
            { id: 'REJECTED', label: 'Declined' },
            { id: 'CANCELLED', label: 'Withdrawn' },
            { id: '', label: 'All Transfers' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                setStatusFilter(tab.id);
                setPage(1);
              }}
              className={`px-3 py-1.5 rounded-xl font-semibold transition ${
                statusFilter === tab.id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="flex items-center justify-between gap-3">
          <div className="relative min-w-[280px]">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search reference, institution, or subject..."
              className="w-full pl-8 pr-3 py-1.5 border border-slate-200 rounded-lg text-xs outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <span className="text-slate-400 text-[11px]">
            Total {total} transfer records
          </span>
        </div>
      </div>

      {/* Queue Table */}
      <div className="bg-white border border-slate-200/80 rounded-2xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500 text-xs flex items-center justify-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
            Loading transfers...
          </div>
        ) : error ? (
          <div className="p-8 text-center text-rose-600 text-xs">
            <AlertCircle className="w-6 h-6 mx-auto mb-2 text-rose-500" />
            {error}
          </div>
        ) : filteredTransfers.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs space-y-2">
            <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-500" />
            <p className="font-medium text-slate-700">No transfer records found.</p>
            <p className="text-[11px] text-slate-400">
              {activeTab === 'INCOMING'
                ? 'Your Bureau has no incoming transfer proposals awaiting action.'
                : 'No outgoing transfer proposals match the current filter.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200/80 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">ID</th>
                  <th className="py-3 px-4">Case Reference</th>
                  <th className="py-3 px-4">Institution</th>
                  <th className="py-3 px-4">Handover Path</th>
                  <th className="py-3 px-4">Transfer Reason</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Initiated</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredTransfers.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/60 transition">
                    <td className="py-3 px-4 font-mono text-slate-400">
                      #{item.id}
                    </td>

                    <td className="py-3 px-4">
                      <Link
                        to={`/aicte/cases/${item.case_id}`}
                        className="font-mono font-bold text-blue-600 hover:underline block"
                      >
                        {item.case_reference}
                      </Link>
                      <p className="text-[11px] text-slate-600 truncate max-w-[200px] mt-0.5" title={item.case_subject}>
                        {item.case_subject}
                      </p>
                    </td>

                    <td className="py-3 px-4 max-w-[190px]">
                      <p className="font-semibold text-slate-800 truncate" title={item.institution_name}>
                        {item.institution_name}
                      </p>
                      <p className="font-mono text-[10px] text-slate-400">
                        {item.institution_aicte_pid || 'PID Pending'}
                      </p>
                    </td>

                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5 font-mono text-[11px]">
                        <span className="px-1.5 py-0.5 bg-slate-100 text-slate-700 font-bold rounded">
                          {item.from_unit_code}
                        </span>
                        <span className="text-slate-400">➔</span>
                        <span className="px-1.5 py-0.5 bg-blue-50 text-blue-700 font-bold rounded border border-blue-200">
                          {item.to_unit_code}
                        </span>
                      </div>
                    </td>

                    <td className="py-3 px-4 max-w-[220px]">
                      <p className="text-[11px] text-slate-700 line-clamp-2" title={item.transfer_reason}>
                        {item.transfer_reason}
                      </p>
                      {item.response_notes && (
                        <p className="text-[10px] text-slate-500 italic mt-0.5 line-clamp-1" title={item.response_notes}>
                          Response: "{item.response_notes}"
                        </p>
                      )}
                    </td>

                    <td className="py-3 px-4">
                      {getStatusBadge(item.transfer_status)}
                    </td>

                    <td className="py-3 px-4 text-slate-500 text-[11px]">
                      <div>{new Date(item.initiated_at).toLocaleDateString()}</div>
                      <span className="text-[10px] text-slate-400">by {item.initiated_by_name}</span>
                    </td>

                    {/* Actions */}
                    <td className="py-3 px-4 text-right">
                      {item.transfer_status === 'PENDING_ACCEPTANCE' ? (
                        activeTab === 'INCOMING' ? (
                          <div className="inline-flex items-center gap-1.5">
                            <button
                              onClick={() => {
                                setSelectedTransfer(item);
                                setDecisionAction('ACCEPT');
                              }}
                              className="px-2.5 py-1 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition font-semibold text-[11px] flex items-center gap-1"
                            >
                              <Check className="w-3.5 h-3.5" />
                              Accept
                            </button>
                            <button
                              onClick={() => {
                                setSelectedTransfer(item);
                                setDecisionAction('REJECT');
                              }}
                              className="px-2.5 py-1 border border-rose-200 text-rose-700 bg-rose-50 rounded-lg hover:bg-rose-100 transition font-semibold text-[11px] flex items-center gap-1"
                            >
                              <X className="w-3.5 h-3.5" />
                              Decline
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => {
                              setSelectedTransfer(item);
                              setDecisionAction('CANCEL');
                            }}
                            className="px-2.5 py-1 border border-slate-200 text-slate-600 rounded-lg hover:bg-slate-100 transition font-medium text-[11px] flex items-center gap-1"
                          >
                            <Ban className="w-3.5 h-3.5" />
                            Withdraw
                          </button>
                        )
                      ) : (
                        <span className="text-[11px] text-slate-400">Closed</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="p-3 border-t border-slate-200/80 bg-slate-50/50 flex items-center justify-between text-xs text-slate-500">
            <span>
              Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, total)} of {total} records
            </span>
            <div className="flex items-center gap-1">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="p-1 rounded border border-slate-200 hover:bg-slate-100 disabled:opacity-40 transition"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="px-2 font-medium">Page {page} of {totalPages}</span>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
                className="p-1 rounded border border-slate-200 hover:bg-slate-100 disabled:opacity-40 transition"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Decision Modal */}
      {selectedTransfer && decisionAction && (
        <TransferDecisionModal
          isOpen={!!selectedTransfer}
          onClose={() => {
            setSelectedTransfer(null);
            setDecisionAction(null);
          }}
          onSuccess={loadTransfers}
          transfer={selectedTransfer}
          actionType={decisionAction}
        />
      )}
    </div>
  );
};
