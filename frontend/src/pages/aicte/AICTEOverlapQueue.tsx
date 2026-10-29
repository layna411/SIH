import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  AICTECaseOverlap, 
  AICTEOverlapReviewStatus, 
  AICTEOverlapType,
  OverlapReviewPayload 
} from '../../types';
import { api } from '../../services/api';
import { AICTEOverlapReviewModal } from './AICTEOverlapReviewModal';
import { 
  Layers, 
  Filter, 
  Search, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  ExternalLink, 
  ArrowRightLeft,
  ShieldAlert,
  ChevronLeft,
  ChevronRight,
  Eye,
  CheckSquare
} from 'lucide-react';

export const AICTEOverlapQueue: React.FC = () => {
  const navigate = useNavigate();
  const [overlaps, setOverlaps] = useState<AICTECaseOverlap[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [reviewStatus, setReviewStatus] = useState<string>('PENDING');
  const [overlapType, setOverlapType] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');

  // Selected for review modal
  const [reviewTarget, setReviewTarget] = useState<AICTECaseOverlap | null>(null);

  useEffect(() => {
    loadOverlaps();
  }, [page, reviewStatus, overlapType]);

  const loadOverlaps = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.append('page', page.toString());
      params.append('page_size', pageSize.toString());
      if (reviewStatus) params.append('review_status', reviewStatus);
      if (overlapType) params.append('overlap_type', overlapType);

      const res = await api.get<{
        items: AICTECaseOverlap[];
        total: number;
        page: number;
        page_size: number;
      }>(`/aicte/overlaps?${params.toString()}`);

      setOverlaps(res.items || []);
      setTotal(res.total || 0);
    } catch (err: any) {
      setError(err?.message || 'Failed to load overlap review queue.');
    } finally {
      setLoading(false);
    }
  };

  const handleReviewSubmit = async (payload: OverlapReviewPayload) => {
    if (!reviewTarget) return;
    try {
      await api.post(`/aicte/overlaps/${reviewTarget.id}/review`, payload);
      setReviewTarget(null);
      await loadOverlaps();
    } catch (err: any) {
      throw new Error(err?.message || 'Failed to record review determination.');
    }
  };

  const getStatusBadge = (status: AICTEOverlapReviewStatus) => {
    const map: Record<AICTEOverlapReviewStatus, { label: string; cls: string }> = {
      PENDING: { label: 'Pending Review', cls: 'bg-amber-50 text-amber-700 border-amber-200' },
      CONFIRMED_DUPLICATE: { label: 'Confirmed Duplicate', cls: 'bg-rose-50 text-rose-700 border-rose-200' },
      CONFIRMED_RELATED: { label: 'Confirmed Related', cls: 'bg-blue-50 text-blue-700 border-blue-200' },
      REJECTED: { label: 'Rejected Match', cls: 'bg-slate-100 text-slate-700 border-slate-200' },
      DEFERRED: { label: 'Deferred', cls: 'bg-yellow-50 text-yellow-700 border-yellow-200' },
    };
    const s = map[status] || { label: status, cls: 'bg-slate-100 text-slate-700' };
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${s.cls}`}>
        {s.label}
      </span>
    );
  };

  const filteredOverlaps = overlaps.filter((item) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const instName = item.case_low?.institution_name?.toLowerCase() || '';
    const pid = item.case_low?.aicte_permanent_id?.toLowerCase() || '';
    const refLow = item.case_low?.case_reference?.toLowerCase() || '';
    const refHigh = item.case_high?.case_reference?.toLowerCase() || '';
    return instName.includes(q) || pid.includes(q) || refLow.includes(q) || refHigh.includes(q);
  });

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="w-6 h-6 text-blue-600" />
            <h1 className="text-xl font-bold text-slate-900">
              Cross-Bureau Overlap & Related Case Review Queue
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Explainable AI-assisted candidate detection for duplicate allegations and related cases across AICTE Bureaus/Cells.
          </p>
        </div>

        <button
          onClick={loadOverlaps}
          className="flex items-center gap-1.5 px-3 py-1.5 border border-slate-200 rounded-xl text-xs font-medium text-slate-600 hover:bg-slate-50 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Queue
        </button>
      </div>

      {/* Statutory Safeguard Card */}
      <div className="p-4 bg-gradient-to-r from-blue-50/80 to-slate-50 border border-blue-200/80 rounded-2xl flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-700 space-y-1">
          <p className="font-bold text-slate-900">Statutory Case Independence & Confidentiality Protection</p>
          <p className="text-[11px] leading-relaxed text-slate-600">
            Confirming an overlap creates an administrative relationship (<code className="font-mono text-blue-700 bg-blue-100/80 px-1 py-0.2 rounded">DUPLICATE_OF</code> or <code className="font-mono text-blue-700 bg-blue-100/80 px-1 py-0.2 rounded">RELATED_TO</code>). Cases are <strong>never merged, closed, or disposed automatically</strong>. Cross-bureau confidential case narratives remain shielded from unauthorized bureau officers.
          </p>
        </div>
      </div>

      {/* Filter Tabs & Search Bar */}
      <div className="p-4 bg-white border border-slate-200/80 rounded-2xl shadow-sm space-y-3">
        {/* Status Tabs */}
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-100 pb-3">
          {[
            { id: 'PENDING', label: 'Pending Review' },
            { id: 'CONFIRMED_DUPLICATE', label: 'Confirmed Duplicates' },
            { id: 'CONFIRMED_RELATED', label: 'Confirmed Related' },
            { id: 'DEFERRED', label: 'Deferred' },
            { id: 'REJECTED', label: 'Rejected' },
            { id: '', label: 'All Records' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                setReviewStatus(tab.id);
                setPage(1);
              }}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
                reviewStatus === tab.id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Secondary Filters & Search */}
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <span className="font-medium text-slate-600">Candidate Type:</span>
            </div>
            <select
              value={overlapType}
              onChange={(e) => {
                setOverlapType(e.target.value);
                setPage(1);
              }}
              className="px-2.5 py-1.5 border border-slate-200 rounded-lg text-xs outline-none focus:ring-1 focus:ring-blue-500 bg-white"
            >
              <option value="">All Overlap Types</option>
              <option value="POTENTIAL_DUPLICATE">Suspected Duplicate</option>
              <option value="RELATED_CASE">Related Case</option>
              <option value="INSUFFICIENT_EVIDENCE">Low Evidence</option>
            </select>
          </div>

          <div className="relative min-w-[260px]">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search reference or institution..."
              className="w-full pl-8 pr-3 py-1.5 border border-slate-200 rounded-lg text-xs outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Table / List */}
      <div className="bg-white border border-slate-200/80 rounded-2xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500 text-xs flex items-center justify-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
            Loading candidates from review queue...
          </div>
        ) : error ? (
          <div className="p-8 text-center text-rose-600 text-xs">
            <AlertCircle className="w-6 h-6 mx-auto mb-2 text-rose-500" />
            {error}
          </div>
        ) : filteredOverlaps.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs space-y-2">
            <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-500" />
            <p className="font-medium text-slate-700">No overlap candidates found for this filter.</p>
            <p className="text-[11px] text-slate-400">All detected cases have been triaged or no pairs match current criteria.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200/80 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">ID</th>
                  <th className="py-3 px-4">Case Docket A</th>
                  <th className="py-3 px-4">Case Docket B</th>
                  <th className="py-3 px-4">Institution</th>
                  <th className="py-3 px-4">Candidate Type</th>
                  <th className="py-3 px-4">Match Score</th>
                  <th className="py-3 px-4">Review Status</th>
                  <th className="py-3 px-4">Detected</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredOverlaps.map((item) => {
                  const reasons = item.match_reasons || {};
                  return (
                    <tr key={item.id} className="hover:bg-slate-50/60 transition">
                      <td className="py-3 px-4 font-mono text-slate-400">
                        #{item.id}
                      </td>

                      {/* Case A */}
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono font-bold text-blue-600">
                            {item.case_low?.case_reference || `#${item.case_id_low}`}
                          </span>
                          {item.case_low?.current_unit_code && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                              {item.case_low.current_unit_code}
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-600 truncate max-w-[180px] mt-0.5" title={item.case_low?.subject}>
                          {item.case_low?.subject || 'N/A'}
                        </p>
                      </td>

                      {/* Case B */}
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono font-bold text-blue-600">
                            {item.case_high?.case_reference || `#${item.case_id_high}`}
                          </span>
                          {item.case_high?.current_unit_code && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                              {item.case_high.current_unit_code}
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-600 truncate max-w-[180px] mt-0.5" title={item.case_high?.subject}>
                          {item.case_high?.subject || 'N/A'}
                        </p>
                      </td>

                      {/* Institution */}
                      <td className="py-3 px-4">
                        <p className="font-semibold text-slate-800 truncate max-w-[190px]">
                          {item.case_low?.institution_name || 'Verified Institution'}
                        </p>
                        <p className="font-mono text-[10px] text-slate-400">
                          {item.case_low?.aicte_permanent_id || item.case_low?.institution_code || 'PID Pending'}
                        </p>
                      </td>

                      {/* Type Badge */}
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                          item.overlap_type === 'POTENTIAL_DUPLICATE'
                            ? 'bg-rose-100 text-rose-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}>
                          {item.overlap_type.replace(/_/g, ' ')}
                        </span>
                        {reasons.cross_bureau && (
                          <span className="block text-[10px] text-purple-700 font-semibold mt-0.5">
                            Cross-Bureau
                          </span>
                        )}
                      </td>

                      {/* Match Score */}
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-1.5">
                          <span className="font-bold text-slate-800">
                            {item.match_score !== null && item.match_score !== undefined
                              ? `${Math.round(item.match_score * 100)}%`
                              : 'Rule'}
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">
                            ({item.detection_method})
                          </span>
                        </div>
                      </td>

                      {/* Review Status */}
                      <td className="py-3 px-4">
                        {getStatusBadge(item.review_status)}
                        {item.active_link_type && (
                          <span className="block text-[10px] text-blue-700 font-mono mt-0.5">
                            Link: {item.active_link_type}
                          </span>
                        )}
                      </td>

                      {/* Detected Date */}
                      <td className="py-3 px-4 text-slate-500 text-[11px]">
                        {new Date(item.detected_at).toLocaleDateString()}
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 text-right">
                        <div className="inline-flex items-center gap-1.5">
                          <button
                            onClick={() => setReviewTarget(item)}
                            className="px-2.5 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded-lg hover:bg-blue-100 transition font-semibold text-[11px] flex items-center gap-1"
                          >
                            <CheckSquare className="w-3.5 h-3.5" />
                            Review
                          </button>
                          <Link
                            to={`/aicte/overlaps/${item.id}`}
                            className="p-1 border border-slate-200 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-50 transition"
                            title="Inspect Details & Signals"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </Link>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
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

      {/* Review Modal */}
      {reviewTarget && (
        <AICTEOverlapReviewModal
          isOpen={!!reviewTarget}
          onClose={() => setReviewTarget(null)}
          onSubmit={handleReviewSubmit}
          overlapId={reviewTarget.id}
          caseLowRef={reviewTarget.case_low?.case_reference || `#${reviewTarget.case_id_low}`}
          caseHighRef={reviewTarget.case_high?.case_reference || `#${reviewTarget.case_id_high}`}
          currentDecision={reviewTarget.review_status}
        />
      )}
    </div>
  );
};
