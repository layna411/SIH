import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Bell, 
  AlertTriangle, 
  ShieldAlert, 
  CheckCircle2, 
  Check, 
  Clock, 
  ExternalLink, 
  Search, 
  Filter, 
  RefreshCw, 
  Sliders, 
  AlertCircle,
  FileText,
  ArrowRightLeft,
  Users,
  ShieldCheck,
  CheckCheck
} from 'lucide-react';
import { api } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { 
  AICTENotification, 
  AICTENotificationListResponse, 
  AICTEAlertSummaryResponse, 
  AICTEOverdueAlertItem,
  AICTEAlertConfiguration 
} from '../../types';

export const AICTENotificationCenter: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.default_role === 'SUPER_ADMIN' || user?.default_role === 'REGULATORY_ADMIN';

  // Tabs: 'alerts' | 'overdue' | 'config'
  const [activeTab, setActiveTab] = useState<'alerts' | 'overdue' | 'config'>('alerts');

  // Filters for alerts tab
  const [filterType, setFilterType] = useState<'ALL' | 'UNREAD' | 'UNACKNOWLEDGED' | 'CRITICAL'>('ALL');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const pageSize = 15;

  // Data states
  const [notifications, setNotifications] = useState<AICTENotification[]>([]);
  const [totalNotifications, setTotalNotifications] = useState<number>(0);
  const [summary, setSummary] = useState<AICTEAlertSummaryResponse | null>(null);
  const [overdueItems, setOverdueItems] = useState<AICTEOverdueAlertItem[]>([]);
  const [totalOverdue, setTotalOverdue] = useState<number>(0);
  const [overduePage, setOverduePage] = useState<number>(1);
  const [config, setConfig] = useState<AICTEAlertConfiguration | null>(null);

  // Loading and action states
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);
  const [configSaving, setConfigSaving] = useState<boolean>(false);
  const [configMessage, setConfigMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [configForm, setConfigForm] = useState({
    warning_window_hours: 48,
    dedup_window_hours: 24,
    transfer_pending_hours: 72,
  });

  // Fetch Summary
  const fetchSummary = async () => {
    try {
      const data = await api.get<AICTEAlertSummaryResponse>('/aicte/alerts/summary');
      setSummary(data);
    } catch {
      // Ignore background error
    }
  };

  // Fetch Notifications List
  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });
      if (filterType === 'UNREAD') params.append('is_read', 'false');
      if (filterType === 'UNACKNOWLEDGED') {
        params.append('is_acknowledged', 'false');
      }
      if (filterType === 'CRITICAL') params.append('severity', 'CRITICAL');
      if (severityFilter && filterType !== 'CRITICAL') params.append('severity', severityFilter);
      if (categoryFilter) params.append('category', categoryFilter);

      const res = await api.get<AICTENotificationListResponse>(`/aicte/notifications?${params.toString()}`);
      setNotifications(res.items || []);
      setTotalNotifications(res.total || 0);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch Overdue Cases Queue
  const fetchOverdueCases = async () => {
    try {
      const res = await api.get<{ items: AICTEOverdueAlertItem[]; total: number }>(
        `/aicte/alerts/overdue?page=${overduePage}&page_size=20`
      );
      setOverdueItems(res.items || []);
      setTotalOverdue(res.total || 0);
    } catch (err) {
      console.error('Failed to load overdue cases:', err);
    }
  };

  // Fetch Alert Configuration
  const fetchConfiguration = async () => {
    try {
      const data = await api.get<AICTEAlertConfiguration>('/aicte/alerts/configuration');
      setConfig(data);
      setConfigForm({
        warning_window_hours: data.warning_window_hours,
        dedup_window_hours: data.dedup_window_hours,
        transfer_pending_hours: data.transfer_pending_hours,
      });
    } catch (err) {
      console.error('Failed to load alert configuration:', err);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  useEffect(() => {
    if (activeTab === 'alerts') {
      fetchNotifications();
    } else if (activeTab === 'overdue') {
      fetchOverdueCases();
    } else if (activeTab === 'config') {
      fetchConfiguration();
    }
  }, [activeTab, page, overduePage, filterType, categoryFilter, severityFilter]);

  // Actions: Mark Read
  const handleMarkRead = async (id: number) => {
    setActionLoadingId(id);
    try {
      await api.post(`/aicte/notifications/${id}/read`);
      setNotifications((prev) =>
        prev.map((item) => (item.id === id ? { ...item, is_read: true } : item))
      );
      fetchSummary();
    } catch (err) {
      console.error('Error marking as read:', err);
    } finally {
      setActionLoadingId(null);
    }
  };

  // Actions: Acknowledge
  const handleAcknowledge = async (id: number) => {
    setActionLoadingId(id);
    try {
      const updated = await api.post<AICTENotification>(`/aicte/notifications/${id}/acknowledge`);
      setNotifications((prev) =>
        prev.map((item) => (item.id === id ? updated : item))
      );
      fetchSummary();
    } catch (err) {
      console.error('Error acknowledging alert:', err);
    } finally {
      setActionLoadingId(null);
    }
  };

  // Actions: Mark All as Read
  const handleMarkAllRead = async () => {
    try {
      await api.post('/aicte/notifications/read-all');
      setNotifications((prev) => prev.map((item) => ({ ...item, is_read: true })));
      fetchSummary();
    } catch (err) {
      console.error('Error marking all as read:', err);
    }
  };

  // Actions: Save Config
  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    setConfigSaving(true);
    setConfigMessage(null);
    try {
      const updated = await api.patch<AICTEAlertConfiguration>('/aicte/alerts/configuration', configForm);
      setConfig(updated);
      setConfigMessage({ type: 'success', text: 'Operational alert thresholds successfully updated and logged to audit trail.' });
    } catch (err: any) {
      setConfigMessage({ type: 'error', text: err.message || 'Failed to update alert configuration.' });
    } finally {
      setConfigSaving(false);
    }
  };

  // Filtered notifications by search query (client-side text filter on current page)
  const displayedNotifications = notifications.filter((item) => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    return (
      item.title.toLowerCase().includes(query) ||
      item.message.toLowerCase().includes(query) ||
      (item.category && item.category.toLowerCase().includes(query)) ||
      (item.reference_id && item.reference_id.toLowerCase().includes(query))
    );
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-50 text-blue-600 rounded-xl">
              <Bell className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">AICTE Centralized Alert Center</h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Role-aware operational notifications, SLA monitoring, and formal alert acknowledgements
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              fetchSummary();
              if (activeTab === 'alerts') fetchNotifications();
              if (activeTab === 'overdue') fetchOverdueCases();
            }}
            className="px-3.5 py-2 text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-xl transition flex items-center gap-1.5"
            title="Refresh alerts"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
          <button
            onClick={handleMarkAllRead}
            className="px-3.5 py-2 text-xs font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-xl transition flex items-center gap-1.5"
          >
            <CheckCheck className="w-4 h-4" /> Mark All as Read
          </button>
        </div>
      </div>

      {/* Operational Metrics Ribbon */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Unread Alerts</span>
            <div className="text-2xl font-black text-slate-900 mt-1">{summary.total_unread}</div>
            <span className="text-[10px] text-slate-500 mt-0.5 block">Requires officer review</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-[11px] font-bold text-red-500 uppercase tracking-wider block">Critical Alerts</span>
            <div className="text-2xl font-black text-red-600 mt-1">{summary.critical_count}</div>
            <span className="text-[10px] text-red-500 mt-0.5 block">Urgent SLA or delivery errors</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-[11px] font-bold text-amber-500 uppercase tracking-wider block">Unacknowledged</span>
            <div className="text-2xl font-black text-amber-600 mt-1">{summary.total_unacknowledged}</div>
            <span className="text-[10px] text-slate-500 mt-0.5 block">Requires confirmation</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-[11px] font-bold text-indigo-500 uppercase tracking-wider block">Overdue Cases</span>
            <div className="text-2xl font-black text-indigo-700 mt-1">{summary.active_overdue_cases_count}</div>
            <span className="text-[10px] text-slate-500 mt-0.5 block">Exceeded configured SLA</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-[11px] font-bold text-purple-500 uppercase tracking-wider block">Pending Transfers</span>
            <div className="text-2xl font-black text-purple-700 mt-1">{summary.pending_transfers_count}</div>
            <span className="text-[10px] text-slate-500 mt-0.5 block">Awaiting Bureau decision</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-[11px] font-bold text-teal-500 uppercase tracking-wider block">Pending Overlaps</span>
            <div className="text-2xl font-black text-teal-700 mt-1">{summary.pending_overlaps_count}</div>
            <span className="text-[10px] text-slate-500 mt-0.5 block">Cross-Bureau candidates</span>
          </div>
        </div>
      )}

      {/* Primary Invariant Notice Banner */}
      <div className="bg-blue-50/70 border border-blue-200 rounded-xl p-3.5 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
        <div className="text-xs text-blue-900 leading-relaxed">
          <span className="font-semibold">AICTE Procedural Principle:</span> Notifications and alert acknowledgements confirm operational awareness only. A notification or acknowledgement never disposes, closes, transfers, or alters a case's official legal status by itself.
        </div>
      </div>

      {/* Main Tabs */}
      <div className="flex border-b border-slate-200 gap-6">
        <button
          onClick={() => { setActiveTab('alerts'); setPage(1); }}
          className={`pb-3 text-xs font-bold transition flex items-center gap-2 border-b-2 ${
            activeTab === 'alerts'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          <Bell className="w-4 h-4" /> Alert Feed ({totalNotifications})
        </button>

        <button
          onClick={() => { setActiveTab('overdue'); setOverduePage(1); }}
          className={`pb-3 text-xs font-bold transition flex items-center gap-2 border-b-2 ${
            activeTab === 'overdue'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          <Clock className="w-4 h-4 text-red-500" /> Live Overdue Cases Queue ({totalOverdue})
        </button>

        {isAdmin && (
          <button
            onClick={() => setActiveTab('config')}
            className={`pb-3 text-xs font-bold transition flex items-center gap-2 border-b-2 ${
              activeTab === 'config'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-900'
            }`}
          >
            <Sliders className="w-4 h-4" /> Alert Thresholds & Policies
          </button>
        )}
      </div>

      {/* TAB 1: Alert Feed */}
      {activeTab === 'alerts' && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => { setFilterType('ALL'); setPage(1); }}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  filterType === 'ALL' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                All
              </button>
              <button
                onClick={() => { setFilterType('UNREAD'); setPage(1); }}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  filterType === 'UNREAD' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                Unread
              </button>
              <button
                onClick={() => { setFilterType('UNACKNOWLEDGED'); setPage(1); }}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  filterType === 'UNACKNOWLEDGED' ? 'bg-amber-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                Requires Ack
              </button>
              <button
                onClick={() => { setFilterType('CRITICAL'); setPage(1); }}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  filterType === 'CRITICAL' ? 'bg-red-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                Critical Only
              </button>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter alert texts..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 w-48"
                />
              </div>

              <select
                value={categoryFilter}
                onChange={(e) => { setCategoryFilter(e.target.value); setPage(1); }}
                className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              >
                <option value="">All Categories</option>
                <option value="SLA_OVERDUE">SLA Overdue</option>
                <option value="SLA_WARNING">SLA Warning</option>
                <option value="TRANSFER_PENDING">Transfer Pending</option>
                <option value="TRANSFER_DECISION">Transfer Decision</option>
                <option value="OVERLAP_PENDING">Overlap Pending</option>
                <option value="OVERLAP_DECISION">Overlap Decision</option>
                <option value="CASE_ASSIGNMENT">Case Assignment</option>
                <option value="CASE_ESCALATED">Case Escalated</option>
                <option value="FAILED_DELIVERY">Failed Delivery</option>
              </select>

              <select
                value={severityFilter}
                onChange={(e) => { setSeverityFilter(e.target.value); setPage(1); }}
                disabled={filterType === 'CRITICAL'}
                className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:opacity-50"
              >
                <option value="">All Severities</option>
                <option value="CRITICAL">Critical</option>
                <option value="WARNING">Warning</option>
                <option value="INFO">Info</option>
              </select>
            </div>
          </div>

          {/* Notifications List */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm divide-y divide-slate-100 overflow-hidden">
            {loading ? (
              <div className="p-12 text-center text-xs text-slate-400">Loading alerts and notifications...</div>
            ) : displayedNotifications.length === 0 ? (
              <div className="p-12 text-center">
                <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
                <h3 className="text-sm font-semibold text-slate-800">No Notifications Matching Filter</h3>
                <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                  There are no alerts matching the selected category, severity, or search parameters.
                </p>
              </div>
            ) : (
              displayedNotifications.map((item) => (
                <div
                  key={item.id}
                  className={`p-4 transition hover:bg-slate-50/70 flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                    !item.is_read ? 'bg-blue-50/15' : ''
                  }`}
                >
                  <div className="flex items-start gap-3.5">
                    <div className="mt-1 shrink-0">
                      {item.severity === 'CRITICAL' ? (
                        <div className="p-2 bg-red-100 text-red-600 rounded-xl">
                          <ShieldAlert className="w-4 h-4" />
                        </div>
                      ) : item.severity === 'WARNING' ? (
                        <div className="p-2 bg-amber-100 text-amber-600 rounded-xl">
                          <AlertTriangle className="w-4 h-4" />
                        </div>
                      ) : (
                        <div className="p-2 bg-blue-100 text-blue-600 rounded-xl">
                          <Bell className="w-4 h-4" />
                        </div>
                      )}
                    </div>

                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                            item.severity === 'CRITICAL'
                              ? 'bg-red-100 text-red-700 border border-red-200'
                              : item.severity === 'WARNING'
                              ? 'bg-amber-100 text-amber-700 border border-amber-200'
                              : 'bg-blue-100 text-blue-700 border border-blue-200'
                          }`}
                        >
                          {item.severity}
                        </span>

                        <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider bg-slate-100 px-2 py-0.5 rounded-full">
                          {item.category || item.notification_type}
                        </span>

                        {!item.is_read && (
                          <span className="w-2 h-2 rounded-full bg-blue-600" title="Unread" />
                        )}

                        <span className="text-[11px] text-slate-400">
                          {new Date(item.created_at).toLocaleString([], {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>

                      <h4 className="text-sm font-semibold text-slate-900">{item.title}</h4>
                      <p className="text-xs text-slate-600 leading-relaxed max-w-2xl">{item.message}</p>

                      {item.is_acknowledged && item.acknowledged_at && (
                        <div className="text-[11px] text-emerald-700 font-medium flex items-center gap-1.5 pt-0.5">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Acknowledged on{' '}
                          {new Date(item.acknowledged_at).toLocaleString([], {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 md:self-center">
                    {item.link && (
                      <Link
                        to={item.link}
                        className="px-3 py-1.5 text-xs font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 rounded-lg transition flex items-center gap-1"
                      >
                        Navigate <ExternalLink className="w-3 h-3" />
                      </Link>
                    )}

                    {item.requires_acknowledgement && !item.is_acknowledged && (
                      <button
                        onClick={() => handleAcknowledge(item.id)}
                        disabled={actionLoadingId === item.id}
                        className="px-3 py-1.5 text-xs font-semibold text-white bg-amber-600 hover:bg-amber-700 rounded-lg transition shadow-sm flex items-center gap-1 disabled:opacity-50"
                      >
                        <Check className="w-3 h-3" /> Acknowledge
                      </button>
                    )}

                    {!item.is_read ? (
                      <button
                        onClick={() => handleMarkRead(item.id)}
                        disabled={actionLoadingId === item.id}
                        className="px-2.5 py-1.5 text-xs font-medium text-slate-500 hover:text-slate-800 transition"
                      >
                        Mark Read
                      </button>
                    ) : (
                      <span className="text-[11px] text-slate-400 font-medium px-2 py-1">Read</span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Pagination */}
          {totalNotifications > pageSize && (
            <div className="flex items-center justify-between px-2 pt-2 text-xs text-slate-500">
              <div>
                Showing {(page - 1) * pageSize + 1} to{' '}
                {Math.min(page * pageSize, totalNotifications)} of {totalNotifications} alerts
              </div>
              <div className="flex items-center gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="px-3 py-1 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 transition font-medium"
                >
                  Previous
                </button>
                <span className="font-semibold text-slate-700">Page {page}</span>
                <button
                  disabled={page * pageSize >= totalNotifications}
                  onClick={() => setPage((p) => p + 1)}
                  className="px-3 py-1 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 transition font-medium"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Live Overdue Cases Queue */}
      {activeTab === 'overdue' && (
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
            <div>
              <h3 className="font-bold text-slate-900 text-sm">Active Cases with Deadline Breaches</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Cases where next action deadlines or expected disposal targets have lapsed
              </p>
            </div>
            <span className="text-xs font-bold text-red-600 bg-red-50 border border-red-200 px-3 py-1 rounded-full">
              {totalOverdue} Cases Overdue
            </span>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden divide-y divide-slate-100">
            {overdueItems.length === 0 ? (
              <div className="p-12 text-center">
                <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
                <h3 className="text-sm font-semibold text-slate-800">No Overdue Cases</h3>
                <p className="text-xs text-slate-400 mt-1">All active institution cases are within SLA deadlines.</p>
              </div>
            ) : (
              overdueItems.map((item) => (
                <div key={item.case_id} className="p-4 hover:bg-slate-50 transition flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-blue-600">{item.case_reference}</span>
                      <span className="text-xs font-semibold text-slate-800">• {item.institution_name}</span>
                      <span className="text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">
                        {item.current_unit_code}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          item.overdue_type === 'BOTH'
                            ? 'bg-red-100 text-red-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}
                      >
                        {item.overdue_type.replace('_', ' ')} OVERDUE ({item.overdue_days}d)
                      </span>
                    </div>

                    <h4 className="text-xs font-medium text-slate-700">{item.subject}</h4>

                    <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-400 pt-1">
                      {item.next_action_due_at && (
                        <span>Next Action Target: {new Date(item.next_action_due_at).toLocaleDateString()}</span>
                      )}
                      {item.expected_disposal_at && (
                        <span>Disposal Target: {new Date(item.expected_disposal_at).toLocaleDateString()}</span>
                      )}
                      <span>Assigned: {item.assigned_officer_name || 'Unassigned'}</span>
                    </div>
                  </div>

                  <Link
                    to={`/aicte/cases/${item.case_id}`}
                    className="px-3.5 py-1.5 text-xs font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition shrink-0 flex items-center gap-1.5 self-start md:self-center"
                  >
                    Open Case File <ExternalLink className="w-3.5 h-3.5" />
                  </Link>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB 3: Alert Configuration (Admins Only) */}
      {activeTab === 'config' && isAdmin && (
        <div className="max-w-2xl bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
          <div>
            <h3 className="font-bold text-slate-900 text-base">Alert Thresholds & Scheduling Policies</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Configure warning windows, deduplication cooldowns, and operational thresholds. Changes are audited.
            </p>
          </div>

          {configMessage && (
            <div
              className={`p-3.5 rounded-xl text-xs flex items-center gap-2 ${
                configMessage.type === 'success'
                  ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                  : 'bg-red-50 text-red-800 border border-red-200'
              }`}
            >
              {configMessage.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 shrink-0" />
              )}
              {configMessage.text}
            </div>
          )}

          <form onSubmit={handleSaveConfig} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Deadline Warning Window (Hours before deadline)
              </label>
              <input
                type="number"
                min="1"
                max="168"
                value={configForm.warning_window_hours}
                onChange={(e) => setConfigForm({ ...configForm, warning_window_hours: parseInt(e.target.value) || 0 })}
                className="w-full text-xs p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">
                Generates SLA_WARNING advisory alerts before next action or disposal targets lapse. (Default: 48h)
              </span>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Scheduler Alert Deduplication Window (Hours)
              </label>
              <input
                type="number"
                min="1"
                max="72"
                value={configForm.dedup_window_hours}
                onChange={(e) => setConfigForm({ ...configForm, dedup_window_hours: parseInt(e.target.value) || 0 })}
                className="w-full text-xs p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">
                Prevents scheduler runs from dispatching repeated alerts for the same condition. (Default: 24h)
              </span>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Delayed Transfer Operational Threshold (Hours)
              </label>
              <input
                type="number"
                min="12"
                max="336"
                value={configForm.transfer_pending_hours}
                onChange={(e) => setConfigForm({ ...configForm, transfer_pending_hours: parseInt(e.target.value) || 0 })}
                className="w-full text-xs p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">
                Hours a proposed transfer can remain pending before triggering a critical operational alert. (Default: 72h)
              </span>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={configSaving}
                className="px-5 py-2.5 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-xl transition shadow-sm disabled:opacity-50"
              >
                {configSaving ? 'Saving Configuration...' : 'Update Threshold Policies'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
