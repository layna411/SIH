import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { api } from '../../services/api';
import { ProceduralActionLog } from './ProceduralActionLog';
import { ProceduralActionModal } from './ProceduralActionModal';
import { AICTECaseRelationships } from './AICTECaseRelationships';
import { InitiateTransferModal } from './InitiateTransferModal';
import { TransferDecisionModal } from './TransferDecisionModal';
import { AICTECaseDetail as AICTECaseDetailType, AddCaseActionPayload, AICTECaseTransfer } from '../../types';
import { 
  Building2, 
  ShieldCheck, 
  Calendar, 
  User, 
  AlertCircle, 
  ArrowLeft, 
  PlusCircle, 
  Clock, 
  FileText, 
  ArrowRightLeft,
  CheckCircle2,
  RefreshCw,
  Send,
  Ban,
  Check,
  X
} from 'lucide-react';

export const AICTECaseDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [caseData, setCaseData] = useState<AICTECaseDetailType | null>(null);
  const [transfers, setTransfers] = useState<AICTECaseTransfer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isActionModalOpen, setIsActionModalOpen] = useState(false);
  const [isTransferModalOpen, setIsTransferModalOpen] = useState(false);
  const [selectedTransferForDecision, setSelectedTransferForDecision] = useState<AICTECaseTransfer | null>(null);
  const [transferDecisionAction, setTransferDecisionAction] = useState<'ACCEPT' | 'REJECT' | 'CANCEL' | null>(null);

  useEffect(() => {
    if (id) {
      loadCaseDetail();
    }
  }, [id]);

  const loadCaseDetail = async () => {
    setLoading(true);
    setError(null);
    try {
      const [data, transferList] = await Promise.all([
        api.get<AICTECaseDetailType>(`/aicte/cases/${id}`),
        api.get<AICTECaseTransfer[]>(`/aicte/cases/${id}/transfers`).catch(() => []),
      ]);
      setCaseData(data);
      setTransfers(transferList || []);
    } catch (err: any) {
      setError(err?.message || 'Failed to load AICTE case details.');
    } finally {
      setLoading(false);
    }
  };

  const handleRecordAction = async (payload: AddCaseActionPayload) => {
    if (!caseData) return;
    await api.post(`/aicte/cases/${caseData.id}/actions`, payload);
    await loadCaseDetail();
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      RECEIVED: 'bg-slate-100 text-slate-700 border-slate-200',
      PENDING_REVIEW: 'bg-amber-50 text-amber-700 border-amber-200',
      UNDER_PROCESS: 'bg-blue-50 text-blue-700 border-blue-200',
      AWAITING_RESPONSE: 'bg-yellow-50 text-yellow-700 border-yellow-200',
      TRANSFER_PENDING: 'bg-orange-50 text-orange-700 border-orange-200',
      TRANSFERRED: 'bg-orange-100 text-orange-800 border-orange-300',
      ESCALATED: 'bg-rose-50 text-rose-700 border-rose-200',
      DISPOSED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      CLOSED: 'bg-slate-100 text-slate-800 border-slate-300',
      REOPENED: 'bg-purple-50 text-purple-700 border-purple-200',
    };
    return (
      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${styles[status] || 'bg-slate-100 text-slate-700'}`}>
        {status.replace('_', ' ')}
      </span>
    );
  };

  const getPriorityBadge = (priority: string) => {
    const styles: Record<string, string> = {
      LOW: 'bg-slate-100 text-slate-600',
      NORMAL: 'bg-blue-50 text-blue-700',
      HIGH: 'bg-amber-50 text-amber-700 font-semibold',
      URGENT: 'bg-rose-50 text-rose-700 font-bold',
    };
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-[11px] uppercase tracking-wide ${styles[priority] || 'bg-slate-100 text-slate-600'}`}>
        {priority} Priority
      </span>
    );
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="flex items-center gap-3 text-slate-500 text-sm">
          <RefreshCw className="w-5 h-5 animate-spin text-blue-600" />
          Loading case docket...
        </div>
      </div>
    );
  }

  if (error || !caseData) {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-center">
          <AlertCircle className="w-8 h-8 text-rose-600 mx-auto mb-2" />
          <h3 className="text-base font-bold text-rose-800 mb-1">Unable to Load Case</h3>
          <p className="text-xs text-rose-600 mb-4">{error || 'Case docket not found or unauthorized.'}</p>
          <div className="flex justify-center gap-3">
            <button
              onClick={() => navigate(-1)}
              className="px-4 py-2 border border-slate-200 bg-white text-slate-700 text-xs rounded-xl hover:bg-slate-50 transition"
            >
              Back
            </button>
            <button
              onClick={loadCaseDetail}
              className="px-4 py-2 bg-blue-600 text-white text-xs rounded-xl hover:bg-blue-700 transition"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Header Breadcrumb & Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/aicte/cases')}
            className="p-2 border border-slate-200 rounded-xl hover:bg-slate-50 text-slate-600 transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900 font-mono tracking-tight">
                {caseData.case_reference}
              </h1>
              {getStatusBadge(caseData.status)}
              {getPriorityBadge(caseData.priority)}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Received: {new Date(caseData.received_at).toLocaleDateString()} | Category: <strong className="text-slate-700">{caseData.category}</strong>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadCaseDetail}
            className="p-2 border border-slate-200 rounded-xl hover:bg-slate-50 text-slate-600 transition text-xs flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
          <button
            onClick={() => setIsTransferModalOpen(true)}
            disabled={caseData.status === 'CLOSED' || caseData.status === 'DISPOSED' || caseData.status === 'TRANSFER_PENDING'}
            className="flex items-center gap-1.5 px-3.5 py-2 border border-purple-200 text-purple-700 bg-purple-50 text-xs font-semibold rounded-xl hover:bg-purple-100 disabled:opacity-50 transition shadow-sm"
          >
            <ArrowRightLeft className="w-4 h-4" />
            Initiate Transfer
          </button>
          <button
            onClick={() => setIsActionModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-xs font-semibold rounded-xl hover:bg-blue-700 transition shadow-sm"
          >
            <PlusCircle className="w-4 h-4" />
            Record Action
          </button>
        </div>
      </div>

      {/* Transfer Pending Warning Banner */}
      {caseData.status === 'TRANSFER_PENDING' && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl flex items-start justify-between gap-3 text-xs text-amber-900">
          <div className="flex items-start gap-2.5">
            <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-slate-900">Inter-Bureau Transfer Proposal Pending Acceptance</p>
              <p className="text-[11px] text-amber-800 mt-0.5 leading-relaxed">
                This case has an active handover proposal awaiting receiving bureau review. Operational responsibility remains with the current unit (<span className="font-bold">{caseData.current_unit_code}</span>) until formally accepted.
              </p>
            </div>
          </div>
          <Link
            to="/aicte/transfers"
            className="px-3 py-1.5 bg-white border border-amber-200 text-amber-900 font-semibold rounded-xl hover:bg-amber-100/70 transition shrink-0"
          >
            Open Transfer Queue →
          </Link>
        </div>
      )}

      {/* Main Grid: Details Left, Timeline Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col (2 cols wide): Case Info & Institution Card */}
        <div className="lg:col-span-2 space-y-6">
          {/* Institution Header Card */}
          <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <div className="p-3 bg-blue-50 text-blue-600 rounded-xl mt-0.5">
                  <Building2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">
                    {caseData.institution_name}
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Code: <span className="font-mono text-slate-700">{caseData.institution_code}</span>
                    {caseData.aicte_permanent_id && (
                      <span className="ml-2 pl-2 border-l border-slate-200">
                        AICTE PID: <span className="font-mono font-semibold text-blue-600">{caseData.aicte_permanent_id}</span>
                      </span>
                    )}
                  </p>
                </div>
              </div>
              <Link
                to={`/aicte/institutions/${caseData.institution_id}`}
                className="text-xs text-blue-600 font-semibold hover:underline flex items-center gap-1"
              >
                Consolidated Profile →
              </Link>
            </div>
          </div>

          {/* Subject & Description Card */}
          <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm space-y-4">
            <div>
              <h2 className="text-base font-bold text-slate-900">{caseData.subject}</h2>
              {caseData.official_reference_number && (
                <p className="text-xs font-mono text-slate-500 mt-1">
                  Official External Ref: <span className="text-slate-800">{caseData.official_reference_number}</span>
                </p>
              )}
            </div>

            <div className="pt-3 border-t border-slate-100">
              <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                Protected Regulatory Narrative
              </h4>
              <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-wrap bg-slate-50/50 p-3.5 rounded-xl border border-slate-100">
                {caseData.description}
              </p>
            </div>

            {/* Referral Banner if Source is Campus Grievance */}
            {caseData.source_type === 'CAMPUS_REFERRAL' && (
              <div className="p-3.5 bg-purple-50 border border-purple-200 rounded-xl flex items-center justify-between text-xs text-purple-900">
                <div className="flex items-center gap-2.5">
                  <ArrowRightLeft className="w-4 h-4 text-purple-600 shrink-0" />
                  <span>
                    Referred from Campus Grievance: <strong>{caseData.source_grievance_ref || `#${caseData.source_grievance_id}`}</strong>
                  </span>
                </div>
                {caseData.source_grievance_id && (
                  <Link
                    to={`/student/grievances/${caseData.source_grievance_id}`}
                    className="font-semibold text-purple-700 hover:underline"
                  >
                    View Original Grievance →
                  </Link>
                )}
              </div>
            )}
          </div>

          {/* Cross-Bureau Overlaps & Case Relationships */}
          <AICTECaseRelationships
            caseId={caseData.id}
            caseReference={caseData.case_reference}
          />

          {/* Inter-Bureau Transfer History Ledger */}
          {transfers.length > 0 && (
            <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                  <ArrowRightLeft className="w-4 h-4 text-purple-600" />
                  Inter-Bureau Transfer Ledger
                </h3>
                <span className="text-xs text-slate-400 font-mono">
                  {transfers.length} Handover{transfers.length === 1 ? '' : 's'}
                </span>
              </div>

              <div className="space-y-2.5 text-xs">
                {transfers.map((t) => (
                  <div key={t.id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-slate-800">
                        {t.from_unit_code} ➔ {t.to_unit_code}
                      </span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                        t.transfer_status === 'ACCEPTED' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                        t.transfer_status === 'REJECTED' ? 'bg-rose-50 text-rose-700 border-rose-200' :
                        t.transfer_status === 'CANCELLED' ? 'bg-slate-100 text-slate-600 border-slate-200' :
                        'bg-amber-50 text-amber-700 border-amber-200'
                      }`}>
                        {t.transfer_status.replace(/_/g, ' ')}
                      </span>
                    </div>

                    <p className="text-slate-800 text-[11px]"><span className="font-semibold text-slate-600">Reason:</span> {t.transfer_reason}</p>
                    {t.handover_summary && (
                      <p className="text-slate-600 text-[11px]"><span className="font-semibold text-slate-600">Handover Summary:</span> {t.handover_summary}</p>
                    )}
                    {t.response_notes && (
                      <p className="text-slate-600 italic text-[11px]"><span className="font-semibold not-italic text-slate-600">Response:</span> "{t.response_notes}"</p>
                    )}

                    <div className="text-[10px] text-slate-400 flex items-center justify-between pt-1 border-t border-slate-200/60">
                      <span>Initiated: {new Date(t.initiated_at).toLocaleDateString()} by {t.initiated_by_name}</span>
                      {t.transfer_status === 'PENDING_ACCEPTANCE' && (
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => {
                              setSelectedTransferForDecision(t);
                              setTransferDecisionAction('ACCEPT');
                            }}
                            className="text-emerald-700 font-bold hover:underline"
                          >
                            Accept
                          </button>
                          <button
                            onClick={() => {
                              setSelectedTransferForDecision(t);
                              setTransferDecisionAction('REJECT');
                            }}
                            className="text-rose-700 font-bold hover:underline"
                          >
                            Decline
                          </button>
                          <button
                            onClick={() => {
                              setSelectedTransferForDecision(t);
                              setTransferDecisionAction('CANCEL');
                            }}
                            className="text-slate-500 font-medium hover:underline"
                          >
                            Withdraw
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Procedural Action Timeline */}
          <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-600" />
                Procedural Case History & Action Ledger
              </h3>
              <span className="text-xs text-slate-400">
                {caseData.actions?.length || 0} Milestone{caseData.actions?.length === 1 ? '' : 's'}
              </span>
            </div>

            <ProceduralActionLog actions={caseData.actions || []} />
          </div>
        </div>

        {/* Right Col: Metadata, Bureau Unit & Next Action Card */}
        <div className="space-y-6">
          {/* Bureau & Officer Assignment Card */}
          <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm space-y-4 text-xs">
            <h3 className="text-sm font-bold text-slate-800 pb-2 border-b border-slate-100 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-blue-600" />
              Organizational Responsibility
            </h3>

            <div>
              <p className="text-slate-500 font-medium">Handling Bureau / Unit</p>
              <div className="mt-1 flex items-center gap-2">
                <span className="px-2 py-0.5 font-bold rounded bg-blue-100 text-blue-800">
                  {caseData.current_unit_code || 'UNASSIGNED'}
                </span>
                <span className="text-slate-800 font-medium truncate">
                  {caseData.current_unit_name}
                </span>
              </div>
            </div>

            <div>
              <p className="text-slate-500 font-medium">Responsible Officer</p>
              <p className="mt-1 text-slate-800 font-semibold flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-slate-400" />
                {caseData.assigned_officer_name || 'Pending Officer Allocation'}
              </p>
              {caseData.assigned_officer_email && (
                <p className="text-[11px] text-slate-400 mt-0.5">{caseData.assigned_officer_email}</p>
              )}
            </div>

            {caseData.region && (
              <div>
                <p className="text-slate-500 font-medium">Jurisdictional Region</p>
                <p className="mt-0.5 text-slate-800 font-medium">{caseData.region}</p>
              </div>
            )}

            <div>
              <p className="text-slate-500 font-medium">Complainant Classification</p>
              <p className="mt-0.5 text-slate-800 font-medium">{caseData.complainant_type.replace(/_/g, ' ')}</p>
            </div>
          </div>

          {/* Next Action & SLA Due Dates */}
          <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm space-y-4 text-xs">
            <h3 className="text-sm font-bold text-slate-800 pb-2 border-b border-slate-100 flex items-center gap-2">
              <Clock className="w-4 h-4 text-amber-600" />
              Deadlines & Expected Milestones
            </h3>

            {caseData.next_action_required ? (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl">
                <p className="text-amber-800 font-semibold mb-1">Next Action Required:</p>
                <p className="text-amber-900">{caseData.next_action_required}</p>
                {caseData.next_action_due_at && (
                  <p className="text-[11px] text-amber-700 mt-2 font-medium">
                    Deadline: {new Date(caseData.next_action_due_at).toLocaleDateString()}
                  </p>
                )}
              </div>
            ) : (
              <p className="text-slate-500 italic">No pending milestone deadline defined.</p>
            )}

            {caseData.expected_disposal_at && (
              <div>
                <p className="text-slate-500 font-medium">Target Statutory Disposal</p>
                <p className="text-slate-800 font-semibold mt-0.5">
                  {new Date(caseData.expected_disposal_at).toLocaleDateString()}
                </p>
              </div>
            )}

            {caseData.disposed_at && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800">
                <p className="font-semibold flex items-center gap-1.5 mb-1">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  Statutorily Disposed
                </p>
                <p className="text-[11px]">
                  Disposal recorded on {new Date(caseData.disposed_at).toLocaleString()}.
                </p>
              </div>
            )}

            <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-400">
              Last Action Timestamp: {new Date(caseData.last_action_at).toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      {/* Record Action Modal */}
      {isActionModalOpen && (
        <ProceduralActionModal
          isOpen={isActionModalOpen}
          onClose={() => setIsActionModalOpen(false)}
          onSubmit={handleRecordAction}
          currentStatus={caseData.status}
          caseReference={caseData.case_reference}
        />
      )}

      {/* Initiate Transfer Modal */}
      {isTransferModalOpen && (
        <InitiateTransferModal
          isOpen={isTransferModalOpen}
          onClose={() => setIsTransferModalOpen(false)}
          onSuccess={loadCaseDetail}
          caseId={caseData.id}
          caseReference={caseData.case_reference}
          currentUnitId={caseData.current_unit_id}
          currentUnitCode={caseData.current_unit_code}
        />
      )}

      {/* Transfer Decision Modal */}
      {selectedTransferForDecision && transferDecisionAction && (
        <TransferDecisionModal
          isOpen={!!selectedTransferForDecision}
          onClose={() => {
            setSelectedTransferForDecision(null);
            setTransferDecisionAction(null);
          }}
          onSuccess={loadCaseDetail}
          transfer={selectedTransferForDecision}
          actionType={transferDecisionAction}
        />
      )}
    </div>
  );
};
