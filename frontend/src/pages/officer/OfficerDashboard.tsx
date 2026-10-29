import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../services/api';
import { Grievance, DashboardStats, GrievanceStatus, GrievancePriority, GrievanceMessageItem } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { PriorityBadge } from '../../components/common/PriorityBadge';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';
import { Modal } from '../../components/common/Modal';
import { 
  Building2, 
  Search, 
  Filter, 
  Clock, 
  AlertTriangle, 
  CheckCircle2, 
  FileText, 
  Eye, 
  ShieldCheck, 
  Send, 
  UserCheck,
  RefreshCw,
  Lock,
  MessageSquare,
  TrendingUp,
  RotateCcw,
  UserPlus
} from 'lucide-react';

export const OfficerDashboard: React.FC = () => {
  const { user } = useAuth();

  const [grievances, setGrievances] = useState<Grievance[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Selected case for management dialog
  const [selectedGrievance, setSelectedGrievance] = useState<Grievance | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [modalTab, setModalTab] = useState<'overview' | 'messages' | 'notes' | 'timeline'>('overview');

  // Status update modal state
  const [isStatusModalOpen, setIsStatusModalOpen] = useState(false);
  const [newStatus, setNewStatus] = useState<GrievanceStatus>('UNDER_REVIEW');
  const [transitionReason, setTransitionReason] = useState('');
  const [resolutionSummary, setResolutionSummary] = useState('');
  const [updatingStatus, setUpdatingStatus] = useState(false);

  // Internal Note state
  const [internalNoteText, setInternalNoteText] = useState('');
  const [addingNote, setAddingNote] = useState(false);

  // Student communication state
  const [studentMessageText, setStudentMessageText] = useState('');
  const [sendingStudentMessage, setSendingStudentMessage] = useState(false);

  // Escalation state
  const [isEscalateModalOpen, setIsEscalateModalOpen] = useState(false);
  const [escalateReason, setEscalateReason] = useState('');
  const [escalateLevel, setEscalateLevel] = useState<'LEVEL_2_INSTITUTION_HEAD' | 'LEVEL_3_REGULATORY'>('LEVEL_2_INSTITUTION_HEAD');
  const [escalating, setEscalating] = useState(false);

  // Claim case state
  const [claiming, setClaiming] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [grvList, statsData] = await Promise.all([
        api.get<Grievance[]>('/grievances'),
        api.get<DashboardStats>('/analytics/dashboard')
      ]);
      setGrievances(grvList);
      setStats(statsData);
    } catch (err) {
      console.error('Failed to load officer dashboard', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openCaseDetails = async (g: Grievance) => {
    try {
      const full = await api.get<Grievance>(`/grievances/${g.id}`);
      setSelectedGrievance(full);
      setModalTab('overview');
      setIsDetailModalOpen(true);
    } catch (err: any) {
      alert(err.message || 'Error loading grievance details.');
    }
  };

  const handleClaimCase = async () => {
    if (!selectedGrievance) return;
    setClaiming(true);
    try {
      const updated = await api.post<Grievance>(`/grievances/${selectedGrievance.id}/claim`);
      setSelectedGrievance(updated);
      alert('Case successfully claimed and assigned to your desk.');
      await fetchData();
    } catch (err: any) {
      alert(err.message || 'Failed to claim grievance.');
    } finally {
      setClaiming(false);
    }
  };

  const handleUpdateStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGrievance || !transitionReason.trim()) return;

    setUpdatingStatus(true);
    try {
      const updated = await api.put<Grievance>(`/grievances/${selectedGrievance.id}/status`, {
        to_status: newStatus,
        reason: transitionReason.trim(),
        resolution_summary: resolutionSummary.trim() || undefined,
      });

      setSelectedGrievance(updated);
      setIsStatusModalOpen(false);
      setTransitionReason('');
      setResolutionSummary('');
      await fetchData();
    } catch (err: any) {
      alert(err.message || 'Failed to update status. Check transition rules.');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleAddInternalNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGrievance || !internalNoteText.trim()) return;

    setAddingNote(true);
    try {
      const note = await api.post<any>(`/grievances/${selectedGrievance.id}/internal-notes`, {
        note: internalNoteText.trim(),
      });
      setSelectedGrievance((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          internal_notes: [note, ...(prev.internal_notes || [])],
        };
      });
      setInternalNoteText('');
    } catch (err: any) {
      alert(err.message || 'Failed to add internal note.');
    } finally {
      setAddingNote(false);
    }
  };

  const handleSendStudentMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGrievance || !studentMessageText.trim()) return;

    setSendingStudentMessage(true);
    try {
      const newMsg = await api.post<GrievanceMessageItem>(`/grievances/${selectedGrievance.id}/messages`, {
        message: studentMessageText.trim(),
      });
      setSelectedGrievance((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          messages: [...(prev.messages || []), newMsg],
        };
      });
      setStudentMessageText('');
    } catch (err: any) {
      alert(err.message || 'Failed to send message to student.');
    } finally {
      setSendingStudentMessage(false);
    }
  };

  const handleEscalateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGrievance || escalateReason.trim().length < 10) {
      alert('Please provide a detailed justification of at least 10 characters.');
      return;
    }

    setEscalating(true);
    try {
      const updated = await api.post<Grievance>(`/grievances/${selectedGrievance.id}/escalate`, {
        reason: escalateReason.trim(),
        level: escalateLevel,
      });
      setSelectedGrievance(updated);
      setIsEscalateModalOpen(false);
      setEscalateReason('');
      alert('Case successfully escalated.');
      await fetchData();
    } catch (err: any) {
      alert(err.message || 'Failed to escalate grievance.');
    } finally {
      setEscalating(false);
    }
  };

  const filteredGrievances = grievances.filter((g) => {
    const matchesSearch = 
      g.title.toLowerCase().includes(search.toLowerCase()) ||
      g.reference_number.toLowerCase().includes(search.toLowerCase()) ||
      g.category_name.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || g.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return <LoadingSpinner message="Accessing institutional grievance desk..." />;
  }

  return (
    <div className="space-y-6">
      {/* Officer Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-md border border-blue-200 uppercase tracking-wide">
              Institutional Grievance Officer Portal
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900">
            Case Queue & Intake Desk
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Reviewing authorized cases for {user?.memberships?.[0]?.institution_name || 'your assigned institution'}.
          </p>
        </div>

        <button
          onClick={fetchData}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Queue
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Active Queue</span>
          <p className="text-2xl font-extrabold text-blue-600">{stats?.pending_grievances || 0}</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Awaiting resolution</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">In Investigation</span>
          <p className="text-2xl font-extrabold text-indigo-600">{stats?.in_investigation_grievances || 0}</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Active inquiry stage</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Overdue Cases</span>
          <p className="text-2xl font-extrabold text-rose-600">{stats?.overdue_grievances || 0}</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Exceeded SLA target</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Resolved (YTD)</span>
          <p className="text-2xl font-extrabold text-emerald-600">{stats?.resolved_grievances || 0}</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Average SLA: {stats?.avg_resolution_days || 0} days</p>
        </div>
      </div>

      {/* Grievances Queue Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        <div className="p-4 sm:p-5 border-b border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search reference, subject or category..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs font-medium text-slate-700 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="SUBMITTED">Submitted (New)</option>
              <option value="UNDER_REVIEW">Under Review</option>
              <option value="ASSIGNED">Assigned</option>
              <option value="INVESTIGATION_IN_PROGRESS">Investigating</option>
              <option value="NEEDS_INFORMATION">Needs Information</option>
              <option value="RESOLUTION_PROPOSED">Resolution Proposed</option>
              <option value="RESOLVED">Resolved</option>
              <option value="ESCALATED">Escalated</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>
        </div>

        {filteredGrievances.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No complaints in queue"
              description="No grievances currently match your filter criteria."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/70 border-b border-slate-100 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Ref #</th>
                  <th className="py-3 px-4">Subject</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4">Due Date</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {filteredGrievances.map((g) => (
                  <tr key={g.id} className="hover:bg-slate-50/60 transition">
                    <td className="py-3.5 px-4 font-mono font-semibold text-slate-900">
                      {g.reference_number}
                    </td>
                    <td className="py-3.5 px-4 max-w-xs sm:max-w-md">
                      <p className="font-semibold text-slate-900 truncate">{g.title}</p>
                      {g.is_confidential && (
                        <span className="inline-flex items-center gap-1 text-[10px] text-amber-600 font-medium">
                          <Lock className="w-2.5 h-2.5" /> Confidential Mode
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-slate-600 whitespace-nowrap">
                      {g.category_name}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <StatusBadge status={g.status} />
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <PriorityBadge priority={g.priority} />
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap text-slate-500">
                      {g.due_date ? new Date(g.due_date).toLocaleDateString() : '—'}
                    </td>
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <button
                        onClick={() => openCaseDetails(g)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 font-semibold text-xs transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        Manage Case
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Case Management Modal */}
      {selectedGrievance && (
        <Modal
          isOpen={isDetailModalOpen}
          onClose={() => setIsDetailModalOpen(false)}
          title={`Case Management #${selectedGrievance.reference_number}`}
          maxWidth="2xl"
        >
          <div className="space-y-4 text-xs text-slate-700">
            {/* Modal Tabs */}
            <div className="flex border-b border-slate-200">
              <button
                onClick={() => setModalTab('overview')}
                className={`px-4 py-2 font-semibold text-xs border-b-2 transition ${
                  modalTab === 'overview'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                Overview & Details
              </button>
              <button
                onClick={() => setModalTab('messages')}
                className={`px-4 py-2 font-semibold text-xs border-b-2 transition flex items-center gap-1.5 ${
                  modalTab === 'messages'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5" />
                Student Chat ({selectedGrievance.messages?.length || 0})
              </button>
              <button
                onClick={() => setModalTab('notes')}
                className={`px-4 py-2 font-semibold text-xs border-b-2 transition flex items-center gap-1.5 ${
                  modalTab === 'notes'
                    ? 'border-purple-600 text-purple-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                Internal Notes ({selectedGrievance.internal_notes?.length || 0})
              </button>
              <button
                onClick={() => setModalTab('timeline')}
                className={`px-4 py-2 font-semibold text-xs border-b-2 transition flex items-center gap-1.5 ${
                  modalTab === 'timeline'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                <Clock className="w-3.5 h-3.5" />
                Audit Timeline
              </button>
            </div>

            {/* TAB 1: OVERVIEW */}
            {modalTab === 'overview' && (
              <div className="space-y-4">
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-sm text-slate-900">{selectedGrievance.title}</span>
                    <StatusBadge status={selectedGrievance.status} />
                  </div>
                  <p className="text-slate-600 whitespace-pre-wrap leading-relaxed">{selectedGrievance.description}</p>
                  
                  <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-slate-200/80 text-[11px]">
                    <div>
                      <span className="text-slate-400 block">Student:</span>
                      <span className="font-semibold text-slate-800">{selectedGrievance.student_name || 'Protected'}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Enrollment ID:</span>
                      <span className="font-semibold text-slate-800">{selectedGrievance.student_id_number || 'Protected'}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Category:</span>
                      <span className="font-semibold text-slate-800">{selectedGrievance.category_name}</span>
                    </div>
                  </div>
                </div>

                {selectedGrievance.resolution_summary && (
                  <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-900">
                    <span className="font-bold block text-xs mb-1">Current Resolution Summary:</span>
                    <p className="text-xs whitespace-pre-wrap">{selectedGrievance.resolution_summary}</p>
                  </div>
                )}

                {/* Officer Action Bar */}
                <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100">
                  <button
                    onClick={() => setIsStatusModalOpen(true)}
                    className="px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition shadow-sm"
                  >
                    Update Case Status
                  </button>

                  <button
                    onClick={handleClaimCase}
                    disabled={claiming}
                    className="px-3.5 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs transition flex items-center gap-1.5"
                  >
                    <UserCheck className="w-3.5 h-3.5 text-blue-600" />
                    {claiming ? 'Claiming...' : 'Claim This Case'}
                  </button>

                  <button
                    onClick={() => setIsEscalateModalOpen(true)}
                    className="px-3.5 py-2 rounded-xl border border-rose-200 bg-rose-50 hover:bg-rose-100 text-rose-700 font-semibold text-xs transition flex items-center gap-1.5"
                  >
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Escalate Case
                  </button>
                </div>
              </div>
            )}

            {/* TAB 2: STUDENT MESSAGES */}
            {modalTab === 'messages' && (
              <div className="space-y-3">
                <div className="max-h-56 overflow-y-auto space-y-3 p-3 bg-slate-50 rounded-xl border border-slate-100">
                  {(!selectedGrievance.messages || selectedGrievance.messages.length === 0) ? (
                    <p className="text-slate-400 text-xs italic text-center py-6">No communication exchanged with student yet.</p>
                  ) : (
                    selectedGrievance.messages.map((m) => {
                      const isOfficer = m.sender_role !== 'STUDENT';
                      return (
                        <div key={m.id} className={`flex flex-col ${isOfficer ? 'items-end' : 'items-start'}`}>
                          <div className="flex items-center gap-1.5 mb-0.5 text-[10px] text-slate-400">
                            <span className="font-semibold text-slate-700">{m.sender_name}</span>
                            <span>({m.sender_role.replace('_', ' ')})</span>
                            <span>•</span>
                            <span>{new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                          </div>
                          <div className={`p-2.5 rounded-xl text-xs max-w-sm ${isOfficer ? 'bg-blue-600 text-white' : 'bg-white border border-slate-200 text-slate-800'}`}>
                            {m.message}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>

                <form onSubmit={handleSendStudentMessage} className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Message the student for clarification or update..."
                    value={studentMessageText}
                    onChange={(e) => setStudentMessageText(e.target.value)}
                    className="flex-1 px-3 py-2 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    type="submit"
                    disabled={sendingStudentMessage || !studentMessageText.trim()}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-xs transition disabled:opacity-50 flex items-center gap-1.5"
                  >
                    <Send className="w-3.5 h-3.5" />
                    Send
                  </button>
                </form>
              </div>
            )}

            {/* TAB 3: INTERNAL NOTES */}
            {modalTab === 'notes' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-purple-700 font-semibold bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                    Confidential Internal Staff Notes (Shielded from student view)
                  </span>
                </div>

                <form onSubmit={handleAddInternalNote} className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Add confidential officer memo or inquiry note..."
                    value={internalNoteText}
                    onChange={(e) => setInternalNoteText(e.target.value)}
                    className="flex-1 px-3 py-2 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                  <button
                    type="submit"
                    disabled={addingNote || !internalNoteText.trim()}
                    className="px-3.5 py-2 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-xl text-xs transition disabled:opacity-50"
                  >
                    Add Note
                  </button>
                </form>

                <div className="space-y-2 max-h-56 overflow-y-auto">
                  {(!selectedGrievance.internal_notes || selectedGrievance.internal_notes.length === 0) ? (
                    <p className="text-slate-400 text-[11px] italic text-center py-6">No internal notes added yet.</p>
                  ) : (
                    selectedGrievance.internal_notes.map((n) => (
                      <div key={n.id} className="p-2.5 rounded-xl bg-purple-50/50 border border-purple-100 text-slate-700">
                        <p className="text-xs">{n.note}</p>
                        <span className="text-[10px] text-purple-600 font-semibold block mt-1">
                          By {n.author_name} • {new Date(n.created_at).toLocaleString()}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* TAB 4: AUDIT TIMELINE */}
            {modalTab === 'timeline' && (
              <div className="space-y-3 max-h-60 overflow-y-auto pl-4 border-l-2 border-slate-100">
                {selectedGrievance.status_history?.map((h) => (
                  <div key={h.id} className="relative pb-3">
                    <span className="font-bold text-xs text-slate-800">{h.to_status.replace('_', ' ')}</span>
                    <p className="text-[11px] text-slate-500 mt-0.5">{h.reason}</p>
                    <span className="text-[10px] text-slate-400 block mt-0.5">
                      By {h.changed_by_name} • {new Date(h.created_at).toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Modal>
      )}

      {/* Status Update Dialog */}
      {selectedGrievance && (
        <Modal
          isOpen={isStatusModalOpen}
          onClose={() => setIsStatusModalOpen(false)}
          title={`Update Status: #${selectedGrievance.reference_number}`}
          maxWidth="md"
        >
          <form onSubmit={handleUpdateStatus} className="space-y-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Target Status *</label>
              <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value as GrievanceStatus)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              >
                <option value="UNDER_REVIEW">Under Review</option>
                <option value="ASSIGNED">Assigned</option>
                <option value="INVESTIGATION_IN_PROGRESS">Investigation In Progress</option>
                <option value="NEEDS_INFORMATION">Needs Student Information</option>
                <option value="RESOLUTION_PROPOSED">Resolution Proposed</option>
                <option value="RESOLVED">Resolved</option>
                <option value="REJECTED">Rejected</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Mandatory Reason for Transition *
              </label>
              <textarea
                rows={3}
                required
                placeholder="Explain the justification for this workflow change (audited)..."
                value={transitionReason}
                onChange={(e) => setTransitionReason(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
              ></textarea>
            </div>

            {['RESOLUTION_PROPOSED', 'RESOLVED'].includes(newStatus) && (
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Resolution Summary
                </label>
                <textarea
                  rows={3}
                  placeholder="Detail the corrective actions taken or settlement reached..."
                  value={resolutionSummary}
                  onChange={(e) => setResolutionSummary(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                ></textarea>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setIsStatusModalOpen(false)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={updatingStatus || !transitionReason.trim()}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold transition disabled:opacity-50"
              >
                {updatingStatus ? 'Applying...' : 'Confirm Update'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Escalate Dialog */}
      {selectedGrievance && (
        <Modal
          isOpen={isEscalateModalOpen}
          onClose={() => setIsEscalateModalOpen(false)}
          title={`Escalate Grievance: #${selectedGrievance.reference_number}`}
          maxWidth="md"
        >
          <form onSubmit={handleEscalateCase} className="space-y-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Escalation Authority Level *</label>
              <select
                value={escalateLevel}
                onChange={(e) => setEscalateLevel(e.target.value as any)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              >
                <option value="LEVEL_2_INSTITUTION_HEAD">Level 2: Institution Head / Director</option>
                <option value="LEVEL_3_REGULATORY">Level 3: Regional Regulatory Council</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Justification for Escalation (Min. 10 characters) *
              </label>
              <textarea
                rows={3}
                required
                minLength={10}
                placeholder="Explain procedural bottleneck or necessity for supervisory review..."
                value={escalateReason}
                onChange={(e) => setEscalateReason(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
              ></textarea>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setIsEscalateModalOpen(false)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={escalating || escalateReason.trim().length < 10}
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-semibold transition disabled:opacity-50"
              >
                {escalating ? 'Escalating...' : 'Confirm Escalation'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
