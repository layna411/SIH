import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../services/api';
import { 
  DashboardStats, 
  Grievance, 
  User, 
  UserInvitation, 
  UserInviteResponse 
} from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { PriorityBadge } from '../../components/common/PriorityBadge';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
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
  CartesianGrid 
} from 'recharts';
import { 
  Building2, 
  Download, 
  AlertTriangle, 
  TrendingUp, 
  CheckCircle2, 
  Layers,
  FileSpreadsheet,
  Zap,
  Users,
  UserPlus,
  Mail,
  Copy,
  Check,
  RotateCcw,
  AlertCircle
} from 'lucide-react';

const COLORS = ['#2563EB', '#6366F1', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981', '#06B6D4'];

export const HeadDashboard: React.FC = () => {
  const { user } = useAuth();
  const location = useLocation();

  const [activeTab, setActiveTab] = useState<'overview' | 'escalations' | 'officers'>('overview');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [escalatedCases, setEscalatedCases] = useState<Grievance[]>([]);
  const [officers, setOfficers] = useState<User[]>([]);
  const [invitations, setInvitations] = useState<UserInvitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingEscalations, setProcessingEscalations] = useState(false);
  const [escalationResult, setEscalationResult] = useState<string | null>(null);
  const [exportingCSV, setExportingCSV] = useState(false);

  // Invite Officer Modal state
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [inviteFullName, setInviteFullName] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteDept, setInviteDept] = useState('Academic Affairs');
  const [inviteDesignation, setInviteDesignation] = useState('');
  const [inviteStaffId, setInviteStaffId] = useState('');
  const [inviting, setInviting] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);

  // Success Modal
  const [successModalOpen, setSuccessModalOpen] = useState(false);
  const [createdInvite, setCreatedInvite] = useState<UserInviteResponse | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);

  // Synchronize route with activeTab
  useEffect(() => {
    if (location.pathname.includes('/head/officers')) {
      setActiveTab('officers');
    } else if (location.pathname.includes('/head/escalations')) {
      setActiveTab('escalations');
    } else {
      setActiveTab('overview');
    }
  }, [location.pathname]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [statsData, grvs, officersData, invData] = await Promise.allSettled([
        api.get<DashboardStats>('/analytics/dashboard'),
        api.get<Grievance[]>('/grievances?status=ESCALATED'),
        api.get<User[]>('/users?role=COLLEGE_OFFICER'),
        api.get<UserInvitation[]>('/users/invitations/list')
      ]);

      if (statsData.status === 'fulfilled') setStats(statsData.value);
      if (grvs.status === 'fulfilled') setEscalatedCases(grvs.value);
      if (officersData.status === 'fulfilled') setOfficers(officersData.value);
      if (invData.status === 'fulfilled') setInvitations(invData.value);
    } catch (err) {
      console.error('Failed to load head dashboard', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleExportCSV = async () => {
    setExportingCSV(true);
    try {
      await api.downloadFile('/analytics/export/csv', 'institutional_grievance_report.csv');
    } catch (err: any) {
      alert(err.message || 'Failed to download institutional report.');
    } finally {
      setExportingCSV(false);
    }
  };

  const handleProcessEscalations = async () => {
    if (!window.confirm('Trigger the automated SLA escalation check? Any cases breaching resolution deadlines will be automatically flagged for institutional intervention.')) {
      return;
    }
    setProcessingEscalations(true);
    setEscalationResult(null);
    try {
      const res = await api.post<{ escalated_count: number; escalated_reference_numbers: string[] }>('/grievances/escalations/process-overdue');
      if (res.escalated_count > 0) {
        setEscalationResult(`Successfully escalated ${res.escalated_count} overdue grievance(s): ${res.escalated_reference_numbers.join(', ')}`);
      } else {
        setEscalationResult('All grievances are currently compliant within SLA deadlines. No cases required escalation.');
      }
      await fetchDashboardData();
    } catch (err: any) {
      alert(err.message || 'Failed to process overdue escalations.');
    } finally {
      setProcessingEscalations(false);
    }
  };

  const handleToggleOfficerStatus = async (officer: User) => {
    const newStatus = !officer.is_active;
    const actionText = newStatus ? 'activate' : 'deactivate';
    if (!window.confirm(`Are you sure you want to ${actionText} ${officer.full_name}? When deactivated, the officer cannot access grievance workflows, but historical audit trails are strictly preserved.`)) {
      return;
    }
    try {
      const updated = await api.put<User>(`/users/${officer.id}/status`, { is_active: newStatus });
      setOfficers((prev) => prev.map((o) => (o.id === officer.id ? updated : o)));
    } catch (err: any) {
      alert(err.message || `Failed to ${actionText} officer.`);
    }
  };

  const handleInviteOfficer = async (e: React.FormEvent) => {
    e.preventDefault();
    setInviteError(null);
    setInviting(true);

    const instId = user?.memberships?.[0]?.institution_id;
    if (!instId) {
      setInviteError('No authorized institution found for your account.');
      setInviting(false);
      return;
    }

    try {
      const res = await api.post<UserInviteResponse>('/users/invite', {
        email: inviteEmail.trim().toLowerCase(),
        full_name: inviteFullName.trim(),
        role: 'COLLEGE_OFFICER',
        institution_id: instId,
        department: inviteDept,
        designation: inviteDesignation.trim() || undefined,
        staff_id_number: inviteStaffId.trim() || undefined,
      });

      setCreatedInvite(res);
      setIsInviteModalOpen(false);
      setSuccessModalOpen(true);

      // Reset form
      setInviteFullName('');
      setInviteEmail('');
      setInviteDesignation('');
      setInviteStaffId('');

      // Refresh officers & invitations
      const [oData, iData] = await Promise.all([
        api.get<User[]>('/users?role=COLLEGE_OFFICER'),
        api.get<UserInvitation[]>('/users/invitations/list')
      ]);
      setOfficers(oData);
      setInvitations(iData);
    } catch (err: any) {
      setInviteError(err.message || 'Failed to send officer invitation.');
    } finally {
      setInviting(false);
    }
  };

  const handleRevokeInvitation = async (id: number) => {
    if (!window.confirm('Are you sure you want to revoke this officer invitation? The token link will be immediately invalidated.')) {
      return;
    }
    try {
      await api.delete(`/users/invitations/${id}`);
      setInvitations((prev) => prev.map((inv) => (inv.id === id ? { ...inv, status: 'REVOKED' } : inv)));
    } catch (err: any) {
      alert(err.message || 'Failed to revoke invitation.');
    }
  };

  const handleResendInvitation = async (id: number) => {
    try {
      const res = await api.post<UserInviteResponse>(`/users/invitations/${id}/resend`);
      setCreatedInvite(res);
      setSuccessModalOpen(true);
      const invData = await api.get<UserInvitation[]>('/users/invitations/list');
      setInvitations(invData);
    } catch (err: any) {
      alert(err.message || 'Failed to resend invitation.');
    }
  };

  const handleCopyLink = () => {
    if (createdInvite?.invitation_link) {
      navigator.clipboard.writeText(createdInvite.invitation_link);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2500);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Calculating institutional metrics and trends..." />;
  }

  const institutionName = user?.memberships?.[0]?.institution_name || 'Your Higher Education Institution';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-md border border-indigo-200 uppercase tracking-wide">
            Institutional Directorate & Oversight
          </span>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 mt-2">
            Executive Grievance Performance Dashboard
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Institutional overview and officer staff management for {institutionName}.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleProcessEscalations}
            disabled={processingEscalations}
            className="inline-flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-semibold text-xs transition shadow-sm disabled:opacity-50"
            title="Scan for SLA deadline breaches and auto-escalate"
          >
            <Zap className={`w-4 h-4 ${processingEscalations ? 'animate-spin' : 'text-rose-600'}`} />
            {processingEscalations ? 'Processing...' : 'Run SLA Escalation Engine'}
          </button>

          <button
            onClick={() => {
              setInviteError(null);
              setIsInviteModalOpen(true);
            }}
            className="inline-flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition shadow-sm"
          >
            <UserPlus className="w-4 h-4" />
            Invite Officer
          </button>

          <button
            onClick={handleExportCSV}
            disabled={exportingCSV}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs transition shadow-sm disabled:opacity-50"
          >
            <FileSpreadsheet className="w-4 h-4" />
            {exportingCSV ? 'Downloading...' : 'Export Report (CSV)'}
          </button>
        </div>
      </div>

      {escalationResult && (
        <div className="p-4 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-900 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-indigo-600 flex-shrink-0" />
            <span>{escalationResult}</span>
          </div>
          <button 
            onClick={() => setEscalationResult(null)}
            className="text-indigo-500 hover:text-indigo-800 font-bold ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-6 border-b border-slate-200 text-xs font-semibold overflow-x-auto">
        <button
          onClick={() => setActiveTab('overview')}
          className={`pb-3 transition flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'overview'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <TrendingUp className="w-4 h-4" /> Executive Overview
        </button>
        <button
          onClick={() => setActiveTab('escalations')}
          className={`pb-3 transition flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'escalations'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <AlertTriangle className="w-4 h-4 text-rose-500" /> Escalated Cases ({escalatedCases.length})
        </button>
        <button
          onClick={() => setActiveTab('officers')}
          className={`pb-3 transition flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'officers'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <Users className="w-4 h-4 text-indigo-600" /> Manage Officers ({officers.length})
        </button>
      </div>

      {/* Tab 1: Overview */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Total Grievances</span>
              <p className="text-2xl font-extrabold text-slate-900">{stats?.total_grievances || 0}</p>
              <span className="text-[11px] text-slate-400">Recorded this academic year</span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Avg Resolution Time</span>
              <p className="text-2xl font-extrabold text-blue-600">{stats?.avg_resolution_days || 0} <span className="text-xs font-normal text-slate-500">Days</span></p>
              <span className="text-[11px] text-slate-400">Target SLA: 7 Days</span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Overdue / SLA Breach</span>
              <p className="text-2xl font-extrabold text-rose-600">{stats?.overdue_grievances || 0}</p>
              <span className="text-[11px] text-rose-500 font-medium">Requires immediate intervention</span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Active Officers</span>
              <p className="text-2xl font-extrabold text-indigo-600">{officers.filter((o) => o.is_active).length}</p>
              <span className="text-[11px] text-indigo-600 font-medium">Handling grievance queues</span>
            </div>
          </div>

          {/* Analytics Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Monthly Submission Trends */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
              <h3 className="font-bold text-slate-900 text-sm mb-4 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-blue-600" />
                Monthly Submission & Resolution Velocity
              </h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats?.monthly_trends || []}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#64748b' }} />
                    <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
                    <Tooltip />
                    <Bar dataKey="submitted" name="Submitted" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="resolved" name="Resolved" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Category Breakdown */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
              <h3 className="font-bold text-slate-900 text-sm mb-4 flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-600" />
                Departmental & Category Distribution
              </h3>
              <div className="h-64 flex items-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={stats?.category_breakdown || []}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {(stats?.category_breakdown || []).map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Escalations */}
      {activeTab === 'escalations' && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h3 className="font-bold text-slate-900 text-xs">Statutory Escalation Cases Requiring Executive Intervention</h3>
              <p className="text-[11px] text-slate-400 mt-0.5">Complaints escalated due to SLA breach or critical safety sensitivity.</p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Ref #</th>
                  <th className="py-3 px-4">Subject</th>
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Officer Assigned</th>
                  <th className="py-3 px-4">Filing Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {escalatedCases.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400">
                      No escalated grievances currently pending for your institution.
                    </td>
                  </tr>
                ) : (
                  escalatedCases.map((g) => (
                    <tr key={g.id} className="hover:bg-slate-50 transition">
                      <td className="py-3 px-4 font-mono font-bold text-blue-600">{g.reference_number}</td>
                      <td className="py-3 px-4 font-semibold text-slate-800">{g.title}</td>
                      <td className="py-3 px-4"><PriorityBadge priority={g.priority} /></td>
                      <td className="py-3 px-4"><StatusBadge status={g.status} /></td>
                      <td className="py-3 px-4 text-slate-600">{g.assigned_officer_name || 'Unassigned'}</td>
                      <td className="py-3 px-4 text-slate-500">{new Date(g.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Manage Officers (Section 5) */}
      {activeTab === 'officers' && (
        <div className="space-y-6">
          {/* Officers Table */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div>
                <h3 className="font-bold text-slate-900 text-xs">Authorized College Grievance Officers</h3>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Officers assigned to handle department-level complaints for {institutionName}.
                </p>
              </div>

              <button
                onClick={() => {
                  setInviteError(null);
                  setIsInviteModalOpen(true);
                }}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition shadow-sm"
              >
                <UserPlus className="w-3.5 h-3.5" />
                Invite Officer
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Officer</th>
                    <th className="py-3 px-4">Email</th>
                    <th className="py-3 px-4">Department</th>
                    <th className="py-3 px-4">Designation</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {officers.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-400">
                        No grievance officers currently registered. Click "Invite Officer" to onboard staff.
                      </td>
                    </tr>
                  ) : (
                    officers.map((officer) => {
                      const membership = officer.memberships?.[0];
                      return (
                        <tr key={officer.id} className="hover:bg-slate-50 transition">
                          <td className="py-3 px-4">
                            <div className="flex items-center gap-2.5">
                              <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white font-bold flex items-center justify-center text-[11px]">
                                {officer.full_name?.charAt(0).toUpperCase()}
                              </div>
                              <span className="font-semibold text-slate-800">{officer.full_name}</span>
                            </div>
                          </td>
                          <td className="py-3 px-4 font-mono text-slate-600 text-[11px]">{officer.email}</td>
                          <td className="py-3 px-4 text-slate-700 font-medium">
                            {membership?.department || 'General Administration'}
                          </td>
                          <td className="py-3 px-4 text-slate-500">
                            {membership?.designation || 'Grievance Officer'}
                          </td>
                          <td className="py-3 px-4">
                            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              officer.is_active
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : 'bg-slate-100 text-slate-500 border border-slate-200'
                            }`}>
                              {officer.is_active ? 'Active' : 'Deactivated'}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right">
                            <button
                              onClick={() => handleToggleOfficerStatus(officer)}
                              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition border ${
                                officer.is_active
                                  ? 'bg-rose-50 text-rose-700 hover:bg-rose-100 border-rose-200'
                                  : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border-emerald-200'
                              }`}
                            >
                              {officer.is_active ? 'Deactivate' : 'Activate'}
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pending Invitations Section */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-100">
              <h3 className="font-bold text-slate-900 text-xs">Pending Officer Invitations</h3>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Single-use invitation links issued for your college.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Candidate</th>
                    <th className="py-3 px-4">Email</th>
                    <th className="py-3 px-4">Department</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Expires</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {invitations.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-slate-400">
                        No pending invitations.
                      </td>
                    </tr>
                  ) : (
                    invitations.map((inv) => (
                      <tr key={inv.id} className="hover:bg-slate-50 transition">
                        <td className="py-3 px-4 font-semibold text-slate-800">{inv.full_name}</td>
                        <td className="py-3 px-4 font-mono text-slate-600 text-[11px]">{inv.email}</td>
                        <td className="py-3 px-4 text-slate-600">{inv.department || 'General'}</td>
                        <td className="py-3 px-4">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            inv.status === 'ACCEPTED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                            inv.status === 'PENDING' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                            'bg-slate-100 text-slate-500 border border-slate-200'
                          }`}>
                            {inv.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-[11px] text-slate-500">
                          {new Date(inv.expires_at).toLocaleDateString()}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <div className="inline-flex items-center gap-2">
                            {inv.status === 'PENDING' && (
                              <button
                                onClick={() => handleRevokeInvitation(inv.id)}
                                className="px-2 py-1 rounded-lg text-[10px] font-semibold bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200"
                              >
                                Revoke
                              </button>
                            )}
                            {inv.status !== 'ACCEPTED' && (
                              <button
                                onClick={() => handleResendInvitation(inv.id)}
                                className="px-2 py-1 rounded-lg text-[10px] font-semibold bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 flex items-center gap-1"
                              >
                                <RotateCcw className="w-3 h-3" /> Resend
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Invite Officer Modal */}
      <Modal
        isOpen={isInviteModalOpen}
        onClose={() => setIsInviteModalOpen(false)}
        title={`Invite College Grievance Officer — ${institutionName}`}
        maxWidth="md"
      >
        <form onSubmit={handleInviteOfficer} className="space-y-4 text-xs">
          {inviteError && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{inviteError}</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Full Name *</label>
              <input
                type="text"
                required
                placeholder="e.g. Prof. Arvind Sharma"
                value={inviteFullName}
                onChange={(e) => setInviteFullName(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Institutional Email *</label>
              <input
                type="email"
                required
                placeholder="officer@college.edu"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Department Scope *</label>
              <select
                value={inviteDept}
                onChange={(e) => setInviteDept(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 text-slate-800"
              >
                <option value="Academic Affairs">Academic Affairs & Teaching</option>
                <option value="Examination Cell">Examination Cell & Evaluation</option>
                <option value="Hostel & Mess">Hostel & Accommodation</option>
                <option value="Finance & Accounts">Finance & Student Accounts</option>
                <option value="Anti-Ragging Cell">Anti-Ragging & Disciplinary</option>
                <option value="Student Welfare">Student Welfare & Mentorship</option>
                <option value="Administration">General Administration</option>
                <option value="Infrastructure">Campus Infrastructure & IT</option>
              </select>
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Designation</label>
              <input
                type="text"
                placeholder="e.g. Hostel Chief Warden"
                value={inviteDesignation}
                onChange={(e) => setInviteDesignation(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300"
              />
            </div>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Faculty / Staff ID Number</label>
            <input
              type="text"
              placeholder="e.g. FAC-2024-042"
              value={inviteStaffId}
              onChange={(e) => setInviteStaffId(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono"
            />
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
            <span className="text-[11px] text-slate-400">
              The officer will receive a secure token to set their password.
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setIsInviteModalOpen(false)}
                className="px-3.5 py-2 rounded-xl border border-slate-200 text-slate-600 font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={inviting}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold flex items-center gap-1.5 disabled:opacity-50"
              >
                {inviting ? 'Generating...' : 'Issue Invitation'}
              </button>
            </div>
          </div>
        </form>
      </Modal>

      {/* Success Modal */}
      <Modal
        isOpen={successModalOpen}
        onClose={() => setSuccessModalOpen(false)}
        title="Officer Invitation Link Generated"
        maxWidth="md"
      >
        <div className="space-y-4 text-xs">
          <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-sm">Invitation Created for {createdInvite?.full_name}</p>
              <p className="text-[11px] text-emerald-700 mt-0.5">
                Department: {createdInvite?.department} • Email: {createdInvite?.email}
              </p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
              Single-Use Onboarding Link (Valid for 7 Days)
            </span>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={createdInvite?.invitation_link || ''}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono text-[11px] bg-white text-slate-700"
              />
              <button
                onClick={handleCopyLink}
                className="px-3 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold flex items-center gap-1.5 shrink-0"
              >
                {copiedLink ? <Check className="w-4 h-4 text-emerald-300" /> : <Copy className="w-4 h-4" />}
                {copiedLink ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-[11px] leading-relaxed">
            <span className="font-bold block mb-0.5">Development Environment Notice:</span>
            SMTP mailer is not currently configured. Share the secure invitation link directly with the officer so they can set their password and activate their departmental account.
          </div>

          <div className="flex justify-end pt-2">
            <button
              onClick={() => setSuccessModalOpen(false)}
              className="px-4 py-2 rounded-xl bg-slate-900 text-white font-semibold"
            >
              Done
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
