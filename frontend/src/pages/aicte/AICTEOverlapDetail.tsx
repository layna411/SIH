import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { AICTECaseOverlap, OverlapReviewPayload, OverlapHistoryItem } from '../../types';
import { api } from '../../services/api';
import { AICTEOverlapReviewModal } from './AICTEOverlapReviewModal';
import { 
  Building2, 
  ShieldCheck, 
  ShieldAlert, 
  AlertCircle, 
  ArrowLeft, 
  CheckCircle2, 
  Clock, 
  Layers, 
  FileText, 
  RefreshCw,
  Lock,
  ArrowRightLeft,
  Sparkles,
  ExternalLink
} from 'lucide-react';

export const AICTEOverlapDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [overlap, setOverlap] = useState<AICTECaseOverlap | null>(null);
  const [history, setHistory] = useState<OverlapHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);

  useEffect(() => {
    if (id) {
      loadDetail();
    }
  }, [id]);

  const loadDetail = async () => {
    setLoading(true);
    setError(null);
    try {
      const [overlapData, historyData] = await Promise.all([
        api.get<AICTECaseOverlap>(`/aicte/overlaps/${id}`),
        api.get<OverlapHistoryItem[]>(`/aicte/overlaps/${id}/history`),
      ]);
      setOverlap(overlapData);
      setHistory(historyData || []);
    } catch (err: any) {
      setError(err?.message || 'Failed to load overlap candidate details.');
    } finally {
      setLoading(false);
    }
  };

  const handleReviewSubmit = async (payload: OverlapReviewPayload) => {
    if (!overlap) return;
    await api.post(`/aicte/overlaps/${overlap.id}/review`, payload);
    await loadDetail();
  };

  const getReviewStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      PENDING: 'bg-amber-50 text-amber-700 border-amber-200',
      CONFIRMED_DUPLICATE: 'bg-rose-50 text-rose-700 border-rose-200',
      CONFIRMED_RELATED: 'bg-blue-50 text-blue-700 border-blue-200',
      REJECTED: 'bg-slate-100 text-slate-700 border-slate-200',
      DEFERRED: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    };
    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${styles[status] || 'bg-slate-100 text-slate-700'}`}>
        {status.replace(/_/g, ' ')}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="flex items-center gap-3 text-slate-500 text-sm">
          <RefreshCw className="w-5 h-5 animate-spin text-blue-600" />
          Loading overlap comparison...
        </div>
      </div>
    );
  }

  if (error || !overlap) {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-center">
          <AlertCircle className="w-8 h-8 text-rose-600 mx-auto mb-2" />
          <h3 className="text-base font-bold text-rose-800 mb-1">Unable to Load Overlap</h3>
          <p className="text-xs text-rose-600 mb-4">{error || 'Overlap record not found or unauthorized.'}</p>
          <button
            onClick={() => navigate('/aicte/overlaps')}
            className="px-4 py-2 border border-slate-200 bg-white text-slate-700 text-xs rounded-xl hover:bg-slate-50 transition"
          >
            Return to Review Queue
          </button>
        </div>
      </div>
    );
  }

  const reasons = overlap.match_reasons || {};

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/aicte/overlaps')}
            className="p-2 border border-slate-200 rounded-xl hover:bg-slate-50 text-slate-600 transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900 font-mono">
                Overlap Candidate #{overlap.id}
              </h1>
              {getReviewStatusBadge(overlap.review_status)}
              <span className={`px-2.5 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider ${
                overlap.overlap_type === 'POTENTIAL_DUPLICATE'
                  ? 'bg-rose-100 text-rose-800'
                  : 'bg-blue-100 text-blue-800'
              }`}>
                {overlap.overlap_type.replace(/_/g, ' ')}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Detected: {new Date(overlap.detected_at).toLocaleString()} | Method: <strong className="text-slate-700">{overlap.detection_method}</strong>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadDetail}
            className="p-2 border border-slate-200 rounded-xl hover:bg-slate-50 text-slate-600 transition text-xs flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
          <button
            onClick={() => setIsReviewModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-xs font-semibold rounded-xl hover:bg-blue-700 transition shadow-sm"
          >
            <CheckCircle2 className="w-4 h-4" />
            Submit Review Determination
          </button>
        </div>
      </div>

      {/* Review Decision Summary Banner if already reviewed */}
      {overlap.review_status !== 'PENDING' && (
        <div className="p-4 bg-slate-50 border border-slate-200/80 rounded-2xl text-xs space-y-1">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-800 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              Recorded Determination: {overlap.review_status.replace(/_/g, ' ')}
            </span>
            <span className="text-slate-400">
              Reviewed: {overlap.reviewed_at ? new Date(overlap.reviewed_at).toLocaleString() : 'N/A'} by {overlap.reviewed_by_name || 'Authorized Officer'}
            </span>
          </div>
          {overlap.review_notes && (
            <p className="text-slate-600 mt-1 italic pl-5">"{overlap.review_notes}"</p>
          )}
          {overlap.active_link_type && (
            <p className="text-blue-700 font-semibold pl-5 pt-1">
              Active Administrative Link: <span className="font-mono bg-blue-100 px-2 py-0.5 rounded">{overlap.active_link_type}</span>
            </p>
          )}
        </div>
      )}

      {/* Explainable Signals Dashboard Card */}
      <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm space-y-4">
        <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-blue-600" />
          Explainable Matching Signals & Confidence Breakdown
        </h3>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
            <span className="text-slate-500 font-medium">Composite Match Score</span>
            <p className="text-xl font-bold text-slate-800 mt-1">
              {overlap.match_score !== null && overlap.match_score !== undefined
                ? `${Math.round(overlap.match_score * 100)}%`
                : 'N/A'}
            </p>
            <span className="text-[10px] text-slate-400">Weighted signal score</span>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
            <span className="text-slate-500 font-medium">Subject Similarity</span>
            <p className="text-xl font-bold text-blue-700 mt-1">
              {Math.round((reasons.subject_similarity || 0) * 100)}%
            </p>
            <span className="text-[10px] text-slate-400">N-gram token overlap</span>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
            <span className="text-slate-500 font-medium">Description Similarity</span>
            <p className="text-xl font-bold text-indigo-700 mt-1">
              {Math.round((reasons.description_similarity || 0) * 100)}%
            </p>
            <span className="text-[10px] text-slate-400">Cosine term frequency</span>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
            <span className="text-slate-500 font-medium">Temporal Proximity</span>
            <p className="text-xl font-bold text-slate-800 mt-1">
              {reasons.temporal_proximity_days ?? 0} Days
            </p>
            <span className="text-[10px] text-slate-400">Difference in filing date</span>
          </div>
        </div>

        {/* Signal Flags & Keyword Pills */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100 text-xs">
          {reasons.same_institution && (
            <span className="px-2.5 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-lg font-medium flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Same Verified Institution
            </span>
          )}
          {reasons.cross_bureau && (
            <span className="px-2.5 py-1 bg-purple-50 text-purple-800 border border-purple-200 rounded-lg font-medium flex items-center gap-1">
              <ArrowRightLeft className="w-3.5 h-3.5 text-purple-600" /> Cross-Bureau Pair ({reasons.unit_low_code} ➔ {reasons.unit_high_code})
            </span>
          )}
          {reasons.category_match && (
            <span className="px-2.5 py-1 bg-blue-50 text-blue-800 border border-blue-200 rounded-lg font-medium">
              Category Agreement: {reasons.category_low}
            </span>
          )}
          {reasons.official_ref_match && (
            <span className="px-2.5 py-1 bg-amber-50 text-amber-800 border border-amber-200 rounded-lg font-medium">
              Official Reference Match
            </span>
          )}
        </div>

        {reasons.shared_keywords && reasons.shared_keywords.length > 0 && (
          <div className="pt-2 text-xs">
            <span className="text-slate-500 font-medium mr-2">Shared Allegation Keywords:</span>
            <div className="inline-flex flex-wrap gap-1 mt-1">
              {reasons.shared_keywords.map((kw: string, i: number) => (
                <span key={i} className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded-md font-mono text-[11px]">
                  {kw}
                </span>
              ))}
            </div>
          </div>
        )}

        <p className="text-xs text-slate-600 italic bg-slate-50 p-3 rounded-xl border border-slate-100">
          <strong>System Rationale:</strong> {reasons.explanation}
        </p>
      </div>

      {/* Side-by-Side Case Comparative Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Case Low */}
        {overlap.case_low && (
          <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Case Docket A</span>
                <Link
                  to={`/aicte/cases/${overlap.case_low.id}`}
                  className="text-base font-bold text-blue-600 hover:underline font-mono flex items-center gap-1.5"
                >
                  {overlap.case_low.case_reference}
                  <ExternalLink className="w-3.5 h-3.5" />
                </Link>
              </div>
              <span className="px-2.5 py-1 rounded font-bold bg-blue-50 text-blue-700 border border-blue-200 text-xs">
                {overlap.case_low.current_unit_code}
              </span>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <p className="text-slate-500 font-medium">Institution</p>
                <p className="font-semibold text-slate-800">{overlap.case_low.institution_name}</p>
                <p className="font-mono text-[10px] text-slate-400">{overlap.case_low.aicte_permanent_id || overlap.case_low.institution_code}</p>
              </div>

              <div>
                <p className="text-slate-500 font-medium">Subject / Allegation</p>
                <p className="font-bold text-slate-900 mt-0.5">{overlap.case_low.subject}</p>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <p className="text-slate-500 font-medium">Category</p>
                  <p className="text-slate-800">{overlap.case_low.category}</p>
                </div>
                <div>
                  <p className="text-slate-500 font-medium">Status</p>
                  <span className="font-medium text-slate-700">{overlap.case_low.status}</span>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <p className="text-slate-500 font-medium">Case Narrative</p>
                  {!overlap.case_low.has_full_access && (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                      <Lock className="w-3 h-3" /> Shielded
                    </span>
                  )}
                </div>
                <p className={`p-3 rounded-xl border text-xs leading-relaxed whitespace-pre-wrap ${
                  overlap.case_low.has_full_access
                    ? 'bg-slate-50/50 border-slate-100 text-slate-700'
                    : 'bg-amber-50/40 border-amber-200/80 text-amber-900 italic'
                }`}>
                  {overlap.case_low.description}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Case High */}
        {overlap.case_high && (
          <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Case Docket B</span>
                <Link
                  to={`/aicte/cases/${overlap.case_high.id}`}
                  className="text-base font-bold text-blue-600 hover:underline font-mono flex items-center gap-1.5"
                >
                  {overlap.case_high.case_reference}
                  <ExternalLink className="w-3.5 h-3.5" />
                </Link>
              </div>
              <span className="px-2.5 py-1 rounded font-bold bg-blue-50 text-blue-700 border border-blue-200 text-xs">
                {overlap.case_high.current_unit_code}
              </span>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <p className="text-slate-500 font-medium">Institution</p>
                <p className="font-semibold text-slate-800">{overlap.case_high.institution_name}</p>
                <p className="font-mono text-[10px] text-slate-400">{overlap.case_high.aicte_permanent_id || overlap.case_high.institution_code}</p>
              </div>

              <div>
                <p className="text-slate-500 font-medium">Subject / Allegation</p>
                <p className="font-bold text-slate-900 mt-0.5">{overlap.case_high.subject}</p>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <p className="text-slate-500 font-medium">Category</p>
                  <p className="text-slate-800">{overlap.case_high.category}</p>
                </div>
                <div>
                  <p className="text-slate-500 font-medium">Status</p>
                  <span className="font-medium text-slate-700">{overlap.case_high.status}</span>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <p className="text-slate-500 font-medium">Case Narrative</p>
                  {!overlap.case_high.has_full_access && (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                      <Lock className="w-3 h-3" /> Shielded
                    </span>
                  )}
                </div>
                <p className={`p-3 rounded-xl border text-xs leading-relaxed whitespace-pre-wrap ${
                  overlap.case_high.has_full_access
                    ? 'bg-slate-50/50 border-slate-100 text-slate-700'
                    : 'bg-amber-50/40 border-amber-200/80 text-amber-900 italic'
                }`}>
                  {overlap.case_high.description}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Audit History Timeline */}
      <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm">
        <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Clock className="w-4 h-4 text-slate-500" />
          Review & Audit Trail History ({history.length} Event{history.length === 1 ? '' : 's'})
        </h3>

        {history.length === 0 ? (
          <p className="text-slate-400 text-xs italic">No prior human review events recorded.</p>
        ) : (
          <div className="space-y-3">
            {history.map((item) => (
              <div key={item.id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs flex items-start justify-between">
                <div>
                  <span className="font-bold text-slate-800 font-mono">{item.action}</span>
                  <p className="text-slate-600 mt-0.5">
                    Actor: <strong className="text-slate-700">{item.actor_name || 'System'}</strong>
                  </p>
                  {item.details && item.details.review_notes && (
                    <p className="text-slate-500 mt-1 italic">"{item.details.review_notes}"</p>
                  )}
                </div>
                <time className="text-[11px] text-slate-400 shrink-0">
                  {new Date(item.timestamp).toLocaleString()}
                </time>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Review Modal */}
      {isReviewModalOpen && overlap && (
        <AICTEOverlapReviewModal
          isOpen={isReviewModalOpen}
          onClose={() => setIsReviewModalOpen(false)}
          onSubmit={handleReviewSubmit}
          overlapId={overlap.id}
          caseLowRef={overlap.case_low?.case_reference || `#${overlap.case_id_low}`}
          caseHighRef={overlap.case_high?.case_reference || `#${overlap.case_id_high}`}
          currentDecision={overlap.review_status}
        />
      )}
    </div>
  );
};
