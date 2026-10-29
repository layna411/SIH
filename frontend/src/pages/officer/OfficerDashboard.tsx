import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../services/api';
import { Grievance, DashboardStats, GrievanceStatus, GrievancePriority, GrievanceMessageItem } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { PriorityBadge } from '../../components/common/PriorityBadge';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';
import { Modal } from '../../components/common/Modal';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
  Legend
} from 'recharts';
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
  UserPlus,
  ShieldAlert,
  BarChart3,
  FileSpreadsheet,
  Download,
  Users,
  Check,
  Activity,
  ArrowRight,
  Layers,
  Inbox
} from 'lucide-react';
import { ReferGrievanceModal } from '../aicte/ReferGrievanceModal';

const CHART_COLORS = ['#2563EB', '#6366F1', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981', '#06B6D4', '#64748B'];

export const OfficerDashboard: React.FC = () => {
  const { user, isBureauMember } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const [pageTab, setPageTab] = useState<'queue' | 'reports'>('queue');
  const [grievances, setGrievances] = useState<Grievance[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [workloadScope, setWorkloadScope] = useState<'MY' | 'UNASSIGNED' | 'OVERDUE' | 'ALL'>('ALL');
  const [exportingCSV, setExportingCSV] = useState(false);

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

  // Refer to AICTE state
  const [isReferModalOpen, setIsReferModalOpen] = useState(false);

  // Synchronize URL route with pageTab
  useEffect(() => {
    if (location.pathname.includes('/officer/reports')) {
      setPageTab('reports');
    } else {
      setPageTab('queue');
    }
  }, [location.pathname]);

  const handleTabChange = (tab: 'queue' | 'reports') => {
    setPageTab(tab);
    if (tab === 'reports') {
      navigate('/officer/reports');
    } else {
      navigate('/officer');
    }
  };

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
    if (!selectedGrievance) return;
    setUpdatingStatus(true);
    try {
      const updated = await api.put<Grievance>(`/grievances/${selectedGrievance.id}/status`, {
        status: newStatus,
        reason: transitionReason.trim(),
        resolution_summary: resolutionSummary.trim() || undefined,
      });
      setSelectedGrievance(updated);
      setIsStatusModalOpen(false);
      setTransitionReason('');
      setResolutionSummary('');
      alert('Grievance status updated successfully.');
      await fetchData();
    } catch (err: any) {
      alert(err.message || 'Failed to update status.');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleAddInternalNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGrievance || !internalNoteText.trim()) return;
    setAddingNote(true);
    try {
      await api.post(`/grievances/${selectedGrievance.id}/notes`, {
        note: internalNoteText.trim(),
      });
      setInternalNoteText('');
      const full = await api.get<Grievance>(`/grievances/${selectedGrievance.id}`);
      setSelectedGrievance(full);
      await fetchData();
    } catch (err: any) {
      alert(err.message || 'Failed to save note.');
    } finally {
      setAddingNote(false);
    }
  };

  const handleSendStudentMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGrievance || !studentMessageText.trim()) return;
    setSendingStudentMessage(true);
    try {
      await api.post(`/grievances/${selectedGrievance.id}/messages`, {
        message: studentMessageText.trim(),
        is_student_visible: true,
      });
      setStudentMessageText('');
      const full = await api.get<Grievance>(`/grievances/${selectedGrievance.id}`);
      setSelectedGrievance(full);
      await fetchData();
    } catch (err: any) {
      alert(err.message || 'Failed to send message.');
    } finally {
      setSendingStudentMessage(false);
    }
  };

  const handleEscalateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGrievance) return;
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

  const handleExportCSV = async () => {
    setExportingCSV(true);
    try {
      await api.downloadFile('/analytics/export/csv', `institutional_grievances_${new Date().toISOString().slice(0, 10)}.csv`);
    } catch (err: any) {
      alert(err.message || 'Failed to download report.');
    } finally {
      setExportingCSV(false);
    }
  };

  // Calculations for Workload
  const myAssignedGrievances = grievances.filter((g) => g.assigned_officer_id === user?.id);
  const myActiveCount = myAssignedGrievances.filter((g) => g.status !== 'RESOLVED' && g.status !== 'CLOSED').length;
  const myResolvedCount = myAssignedGrievances.filter((g) => g.status === 'RESOLVED' || g.status === 'CLOSED').length;
  const unassignedGrievances = grievances.filter((g) => !g.assigned_officer_id);
  const now = new Date();
  const overdueGrievances = grievances.filter(
    (g) => g.status !== 'RESOLVED' && g.status !== 'CLOSED' && g.due_date && new Date(g.due_date) < now
  );

  const filteredGrievances = grievances.filter((g) => {
    const matchesSearch = 
      g.title.toLowerCase().includes(search.toLowerCase()) ||
      g.reference_number.toLowerCase().includes(search.toLowerCase()) ||
      g.category_name.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || g.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const workloadScopedGrievances = grievances.filter((g) => {
    if (workloadScope === 'MY') return g.assigned_officer_id === user?.id;
    if (workloadScope === 'UNASSIGNED') return !g.assigned_officer_id;
    if (workloadScope === 'OVERDUE') {
      return g.status !== 'RESOLVED' && g.status !== 'CLOSED' && g.due_date && new Date(g.due_date) < now;
    }
    return true;
  });

  if (loading) {
    return <LoadingSpinner message="Accessing institutional grievance desk and analytics..." />;
  }

  const institutionName = user?.memberships?.[0]?.institution_name || 'Your Higher Education Institution';

  return (
    <div className="space-y-6">
      {/* Officer Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-md border border-blue-200 uppercase tracking-wide">
              Institutional Grievance Officer Portal
            </span>
            {isBureauMember && (
              <span className="text-xs font-bold text-purple-700 bg-purple-50 px-2.5 py-1 rounded-md border border-purple-200 uppercase tracking-wide flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-purple-600" />
                AICTE Bureau Member
              </span>
            )}
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900">
            {pageTab === 'reports' ? 'Workload, Reports & Performance Analytics' : 'Case Queue & Intake Desk'}
          </h1>
          <p className="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
            <Building2 className="w-3.5 h-3.5 text-slate-400" />
            <span>Authorized operations for <strong>{institutionName}</strong></span>
          </p>
        </div>

        <div className="flex items-center gap-2">
          {pageTab === 'reports' && (
            <button
              onClick={handleExportCSV}
              disabled={exportingCSV}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs transition shadow-sm disabled:opacity-50"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
              {exportingCSV ? 'Downloading...' : 'Export Report (CSV)'}
            </button>
          )}

          <button
            onClick={fetchData}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>
      </div>

      {/* Bureau Officer Banner Link (if active bureau member) */}
      {isBureauMember && (
        <div className="bg-gradient-to-r from-purple-50 via-indigo-50 to-blue-50 border border-purple-200/80 p-4 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-purple-600 text-white flex items-center justify-center shrink-0">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-bold text-purple-950">AICTE Central Bureau Access Enabled</p>
              <p className="text-[11px] text-purple-700">
                You hold active AICTE Bureau credentials. You can access national case queues, inter-bureau transfers, and cross-bureau overlap detection.
              </p>
            </div>
          </div>
          <button
            onClick={() => navigate('/aicte')}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-semibold text-xs transition shrink-0 shadow-sm"
          >
            Open AICTE Operations
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center gap-6 border-b border-slate-200 text-xs font-semibold overflow-x-auto">
        <button
          onClick={() => handleTabChange('queue')}
          className={`pb-3 transition flex items-center gap-2 whitespace-nowrap ${
            pageTab === 'queue'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <Inbox className="w-4 h-4" />
          Case Intake & Queue ({grievances.length})
        </button>

        <button
          onClick={() => handleTabChange('reports')}
          className={`pb-3 transition flex items-center gap-2 whitespace-nowrap ${
            pageTab === 'reports'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          Workload & Reports
        </button>
      </div>

      {/* =========================================================================
          TAB 1: CASE INTAKE & QUEUE
          ========================================================================= */}
      {pageTab === 'queue' && (
        <div className="space-y-6">
          {/* Quick Metrics Row */}
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
              <p className="text-[11px] text-slate-400 mt-0.5">Avg SLA: {stats?.avg_resolution_days || 0} days</p>
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
        </div>
      )}

      {/* =========================================================================
          TAB 2: WORKLOAD & REPORTS
          ========================================================================= */}
      {pageTab === 'reports' && (
        <div className="space-y-6">
          {/* Detailed Workload KPI Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">My Active Cases</span>
              <p className="text-2xl font-extrabold text-blue-600">{myActiveCount}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">{myResolvedCount} resolved by you YTD</p>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Unassigned Pool</span>
              <p className="text-2xl font-extrabold text-amber-600">{unassignedGrievances.length}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">Awaiting officer claim</p>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">SLA Breaches</span>
              <p className="text-2xl font-extrabold text-rose-600">{overdueGrievances.length}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">Exceeded target timeline</p>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Avg Resolution</span>
              <p className="text-2xl font-extrabold text-indigo-600">{stats?.avg_resolution_days || 0} <span className="text-sm font-normal text-slate-400">days</span></p>
              <p className="text-[11px] text-slate-500 mt-0.5">Campus benchmark</p>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm col-span-2 lg:col-span-1">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Satisfaction</span>
              <p className="text-2xl font-extrabold text-emerald-600">{stats?.satisfaction_rate || 92}%</p>
              <p className="text-[11px] text-slate-500 mt-0.5">Student feedback score</p>
            </div>
          </div>

          {/* Visual Performance Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Category Breakdown Chart */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-blue-600" />
                  Grievances by Category
                </h3>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
                  Volume Breakdown
                </span>
              </div>

              {stats?.category_breakdown && stats.category_breakdown.length > 0 ? (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={stats.category_breakdown} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                      <XAxis 
                        dataKey="name" 
                        tick={{ fontSize: 10, fill: '#64748B' }} 
                        angle={-20} 
                        textAnchor="end"
                        interval={0}
                      />
                      <YAxis tick={{ fontSize: 10, fill: '#64748B' }} allowDecimals={false} />
                      <Tooltip 
                        contentStyle={{ borderRadius: '12px', fontSize: '11px', border: '1px solid #CBD5E1' }}
                      />
                      <Bar dataKey="value" name="Grievances" radius={[6, 6, 0, 0]}>
                        {stats.category_breakdown.map((_, index) => (
                          <Cell key={`cat-cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-xs text-slate-400">
                  No categorical grievance data recorded.
                </div>
              )}
            </div>

            {/* Status Breakdown Chart */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <PieChart className="w-4 h-4 text-indigo-600" />
                  Case Status Pipeline
                </h3>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
                  Current State
                </span>
              </div>

              {stats?.status_breakdown && stats.status_breakdown.length > 0 ? (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={stats.status_breakdown}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        innerRadius={55}
                        outerRadius={85}
                        paddingAngle={3}
                        label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                      >
                        {stats.status_breakdown.map((_, index) => (
                          <Cell key={`status-cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={{ borderRadius: '12px', fontSize: '11px', border: '1px solid #CBD5E1' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-xs text-slate-400">
                  No status distribution available.
                </div>
              )}
            </div>
          </div>

          {/* Monthly Intake & Resolution Trends */}
          {stats?.monthly_trends && stats.monthly_trends.length > 0 && (
            <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-emerald-600" />
                  Monthly Intake vs Resolution Rate
                </h3>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
                  6-Month Trend
                </span>
              </div>

              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.monthly_trends} margin={{ top: 10, right: 20, left: -20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                    <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#64748B' }} />
                    <YAxis tick={{ fontSize: 11, fill: '#64748B' }} allowDecimals={false} />
                    <Tooltip contentStyle={{ borderRadius: '12px', fontSize: '11px', border: '1px solid #CBD5E1' }} />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                    <Bar dataKey="submitted" name="New Complaints" fill="#3B82F6" radius={[6, 6, 0, 0]} />
                    <Bar dataKey="resolved" name="Resolved" fill="#10B981" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Workload Caseload Table */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
            <div className="p-4 sm:p-5 border-b border-slate-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Users className="w-4 h-4 text-blue-600" />
                  Caseload & SLA Compliance Report
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Detailed view of operational complaints assigned across institutional officers.
                </p>
              </div>

              {/* Scope filter pills */}
              <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-xl text-xs font-semibold">
                <button
                  onClick={() => setWorkloadScope('ALL')}
                  className={`px-3 py-1.5 rounded-lg transition ${
                    workloadScope === 'ALL' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  All ({grievances.length})
                </button>
                <button
                  onClick={() => setWorkloadScope('MY')}
                  className={`px-3 py-1.5 rounded-lg transition ${
                    workloadScope === 'MY' ? 'bg-white text-blue-600 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Assigned to Me ({myAssignedGrievances.length})
                </button>
                <button
                  onClick={() => setWorkloadScope('UNASSIGNED')}
                  className={`px-3 py-1.5 rounded-lg transition ${
                    workloadScope === 'UNASSIGNED' ? 'bg-white text-amber-600 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Unassigned ({unassignedGrievances.length})
                </button>
                <button
                  onClick={() => setWorkloadScope('OVERDUE')}
                  className={`px-3 py-1.5 rounded-lg transition ${
                    workloadScope === 'OVERDUE' ? 'bg-white text-rose-600 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Overdue ({overdueGrievances.length})
                </button>
              </div>
            </div>

            {workloadScopedGrievances.length === 0 ? (
              <div className="p-8">
                <EmptyState
                  title="No cases in this workload scope"
                  description="There are currently no complaints matching the selected filter."
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
                      <th className="py-3 px-4">Assigned Officer</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Priority</th>
                      <th className="py-3 px-4">SLA Deadline</th>
                      <th className="py-3 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {workloadScopedGrievances.map((g) => {
                      const isBreached = g.status !== 'RESOLVED' && g.status !== 'CLOSED' && g.due_date && new Date(g.due_date) < now;
                      return (
                        <tr key={g.id} className="hover:bg-slate-50/60 transition">
                          <td className="py-3.5 px-4 font-mono font-semibold text-slate-900">
                            {g.reference_number}
                          </td>
                          <td className="py-3.5 px-4 max-w-xs sm:max-w-md">
                            <p className="font-semibold text-slate-900 truncate">{g.title}</p>
                          </td>
                          <td className="py-3.5 px-4 text-slate-600 whitespace-nowrap">
                            {g.category_name}
                          </td>
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            {g.assigned_officer_name ? (
                              <span className="font-medium text-slate-800">{g.assigned_officer_name}</span>
                            ) : (
                              <span className="text-amber-600 font-medium italic">Unassigned</span>
                            )}
                          </td>
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            <StatusBadge status={g.status} />
                          </td>
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            <PriorityBadge priority={g.priority} />
                          </td>
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            {g.due_date ? (
                              <span className={`inline-flex items-center gap-1 font-medium ${isBreached ? 'text-rose-600 font-bold' : 'text-slate-600'}`}>
                                {isBreached && <AlertTriangle className="w-3.5 h-3.5 text-rose-500" />}
                                {new Date(g.due_date).toLocaleDateString()}
                              </span>
                            ) : (
                              <span className="text-slate-400">—</span>
                            )}
                          </td>
                          <td className="py-3.5 px-4 text-right whitespace-nowrap">
                            <button
                              onClick={() => openCaseDetails(g)}
                              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 font-semibold text-xs transition"
                            >
                              <Eye className="w-3.5 h-3.5" />
                              View Case
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* =========================================================================
          CASE MANAGEMENT MODAL (SHARED ACROSS BOTH TABS)
          ========================================================================= */}
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
                      <span className="font-semibold text-slate-800">{selectedGrievance.student_name}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Category:</span>
                      <span className="font-semibold text-slate-800">{selectedGrievance.category_name}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Priority:</span>
                      <PriorityBadge priority={selectedGrievance.priority} />
                    </div>
                  </div>
                </div>

                {/* AI Assist Signals Card */}
                {selectedGrievance.ai_confidence && (
                  <div className="bg-blue-50/60 p-4 rounded-xl border border-blue-200 text-slate-800">
                    <div className="flex items-center gap-2 mb-2">
                      <ShieldAlert className="w-4 h-4 text-blue-600" />
                      <span className="font-bold text-blue-900">EduResolve AI Triage Intelligence</span>
                    </div>
                    <p className="text-slate-600 text-[11px] mb-2">{selectedGrievance.ai_explanation}</p>
                    <div className="flex items-center gap-4 text-[11px] text-blue-800 font-medium">
                      <span>Confidence Score: {Math.round(selectedGrievance.ai_confidence * 100)}%</span>
                      {selectedGrievance.ai_duplicate_suspected && (
                        <span className="text-rose-600 font-bold">⚠️ Suspected Duplicate Reference: {selectedGrievance.ai_duplicate_ref}</span>
                      )}
                    </div>
                  </div>
                )}

                {/* Action Buttons Toolbar */}
                <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100">
                  {!selectedGrievance.assigned_officer_id && (
                    <button
                      onClick={handleClaimCase}
                      disabled={claiming}
                      className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 transition"
                    >
                      <UserCheck className="w-4 h-4" />
                      {claiming ? 'Claiming...' : 'Claim This Case'}
                    </button>
                  )}

                  <button
                    onClick={() => {
                      setNewStatus(selectedGrievance.status);
                      setTransitionReason('');
                      setResolutionSummary('');
                      setIsStatusModalOpen(true);
                    }}
                    className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-50 font-semibold transition"
                  >
                    <RotateCcw className="w-4 h-4 text-blue-600" />
                    Transition Status
                  </button>

                  <button
                    onClick={() => {
                      setEscalateReason('');
                      setIsEscalateModalOpen(true);
                    }}
                    className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 font-semibold transition"
                  >
                    <AlertTriangle className="w-4 h-4 text-rose-600" />
                    Escalate Case
                  </button>

                  <button
                    onClick={() => setIsReferModalOpen(true)}
                    className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100 font-semibold transition"
                  >
                    <ShieldAlert className="w-4 h-4 text-purple-600" />
                    Refer to AICTE
                  </button>
                </div>
              </div>
            )}

            {/* TAB 2: STUDENT MESSAGES */}
            {modalTab === 'messages' && (
              <div className="space-y-4">
                <div className="max-h-64 overflow-y-auto space-y-3 p-3 bg-slate-50 rounded-xl border border-slate-200">
                  {(!selectedGrievance.messages || selectedGrievance.messages.length === 0) ? (
                    <p className="text-center text-slate-400 py-6">No communication recorded with student yet.</p>
                  ) : (
                    selectedGrievance.messages.map((m: GrievanceMessageItem) => (
                      <div 
                        key={m.id} 
                        className={`p-3 rounded-xl max-w-[85%] text-xs ${
                          m.sender_role === 'STUDENT'
                            ? 'bg-white border border-slate-200 text-slate-800 mr-auto'
                            : 'bg-blue-600 text-white ml-auto'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-3 mb-1 text-[10px] opacity-80">
                          <span className="font-semibold">{m.sender_name} ({m.sender_role})</span>
                          <span>{new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                        <p className="whitespace-pre-wrap">{m.message}</p>
                      </div>
                    ))
                  )}
                </div>

                <form onSubmit={handleSendStudentMessage} className="flex gap-2">
                  <input
                    type="text"
                    required
                    placeholder="Type official reply to student..."
                    value={studentMessageText}
                    onChange={(e) => setStudentMessageText(e.target.value)}
                    className="flex-1 px-3 py-2 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    type="submit"
                    disabled={sendingStudentMessage || !studentMessageText.trim()}
                    className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition disabled:opacity-50 flex items-center gap-1"
                  >
                    <Send className="w-3.5 h-3.5" />
                    {sendingStudentMessage ? 'Sending...' : 'Send'}
                  </button>
                </form>
              </div>
            )}

            {/* TAB 3: INTERNAL NOTES */}
            {modalTab === 'notes' && (
              <div className="space-y-4">
                <div className="max-h-64 overflow-y-auto space-y-3 p-3 bg-slate-50 rounded-xl border border-slate-200">
                  {(!selectedGrievance.internal_notes || selectedGrievance.internal_notes.length === 0) ? (
                    <p className="text-center text-slate-400 py-6">No internal notes added. These notes are strictly private to officers.</p>
                  ) : (
                    selectedGrievance.internal_notes.map((n) => (
                      <div key={n.id} className="p-3 bg-white rounded-xl border border-purple-200/60 shadow-xs">
                        <div className="flex items-center justify-between text-[11px] text-purple-900 font-semibold mb-1">
                          <span>{n.author_name}</span>
                          <span className="text-slate-400 text-[10px] font-normal">{new Date(n.created_at).toLocaleString()}</span>
                        </div>
                        <p className="text-slate-700 text-xs whitespace-pre-wrap">{n.note}</p>
                      </div>
                    ))
                  )}
                </div>

                <form onSubmit={handleAddInternalNote} className="space-y-2">
                  <textarea
                    rows={2}
                    required
                    placeholder="Add confidential internal note (only visible to institutional committee & officers)..."
                    value={internalNoteText}
                    onChange={(e) => setInternalNoteText(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-purple-500"
                  ></textarea>
                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={addingNote || !internalNoteText.trim()}
                      className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-semibold text-xs transition disabled:opacity-50"
                    >
                      {addingNote ? 'Saving...' : 'Add Confidential Note'}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* TAB 4: AUDIT TIMELINE */}
            {modalTab === 'timeline' && (
              <div className="space-y-3 max-h-80 overflow-y-auto p-3">
                {(!selectedGrievance.status_history || selectedGrievance.status_history.length === 0) ? (
                  <p className="text-center text-slate-400 py-6">No historical transitions recorded.</p>
                ) : (
                  selectedGrievance.status_history.map((h, i) => (
                    <div key={h.id || i} className="flex gap-3 text-xs">
                      <div className="flex flex-col items-center">
                        <div className="w-2.5 h-2.5 rounded-full bg-blue-600 mt-1"></div>
                        {i < (selectedGrievance.status_history?.length || 0) - 1 && (
                          <div className="w-0.5 h-full bg-slate-200 my-1"></div>
                        )}
                      </div>
                      <div className="flex-1 pb-4">
                        <p className="font-semibold text-slate-800">
                          {h.from_status ? `${h.from_status} → ` : 'Status Initialized: '}
                          <span className="text-blue-600">{h.to_status}</span>
                        </p>
                        <p className="text-[11px] text-slate-500 mt-0.5">{h.reason}</p>
                        <span className="text-[10px] text-slate-400 block mt-1">
                          By {h.changed_by_name} • {new Date(h.created_at).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  ))
                )}
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
                <option value="NEEDS_INFORMATION">Needs Information (Student Clarification)</option>
                <option value="RESOLUTION_PROPOSED">Resolution Proposed</option>
                <option value="RESOLVED">Resolved (Case Finalized)</option>
                <option value="REJECTED">Rejected</option>
                <option value="CLOSED">Closed</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Formal Reason / Audit Note *
              </label>
              <textarea
                rows={3}
                required
                placeholder="Explain the administrative basis for this status transition..."
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

      {/* Refer to AICTE Modal */}
      {selectedGrievance && isReferModalOpen && (
        <ReferGrievanceModal
          isOpen={isReferModalOpen}
          onClose={() => setIsReferModalOpen(false)}
          onSuccess={() => {
            setIsReferModalOpen(false);
            fetchData();
            if (selectedGrievance) {
              openCaseDetails(selectedGrievance);
            }
          }}
          grievanceId={selectedGrievance.id}
          grievanceRef={selectedGrievance.reference_number}
          institutionId={selectedGrievance.institution_id}
        />
      )}
    </div>
  );
};
