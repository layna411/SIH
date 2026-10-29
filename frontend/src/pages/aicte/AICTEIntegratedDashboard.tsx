import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
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
  Legend,
  AreaChart,
  Area
} from 'recharts';
import { 
  ShieldCheck, 
  Layers, 
  Activity, 
  Clock, 
  CheckCircle2, 
  PlusCircle, 
  ArrowRightLeft, 
  Building2, 
  RefreshCw,
  Download,
  AlertTriangle,
  TrendingUp,
  ShieldAlert,
  ArrowRight,
  Filter,
  Calendar,
  AlertCircle
} from 'lucide-react';

import { api } from '../../services/api';
import { 
  AICTEOverviewAnalyticsResponse, 
  AICTEAgeingResponse, 
  AICTESLAResponse,
  AICTETrendsResponse,
  AICTEOrganizationalUnitsAnalyticsResponse,
  AICTEInstitutionsAnalyticsResponse,
  AICTETransferAnalyticsResponse,
  AICTECrossBureauAnalyticsResponse
} from '../../types';
import { CreateAICTECaseModal } from './CreateAICTECaseModal';
import { ReferGrievanceModal } from './ReferGrievanceModal';

const STATUS_COLORS: Record<string, string> = {
  RECEIVED: '#94a3b8',
  PENDING_REVIEW: '#f59e0b',
  UNDER_PROCESS: '#3b82f6',
  AWAITING_RESPONSE: '#eab308',
  TRANSFER_PENDING: '#f97316',
  TRANSFERRED: '#c2410c',
  ESCALATED: '#ef4444',
  DISPOSED: '#10b981',
  CLOSED: '#64748b',
  REOPENED: '#8b5cf6',
};

const AGE_COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#f97316', '#ef4444'];

export const AICTEIntegratedDashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [periodPreset, setPeriodPreset] = useState<'all' | '30d' | '90d' | '180d'>('all');
  const [selectedUnitId, setSelectedUnitId] = useState<string>('');
  const [selectedRegion, setSelectedRegion] = useState<string>('');
  
  // Data states
  const [overview, setOverview] = useState<AICTEOverviewAnalyticsResponse | null>(null);
  const [ageing, setAgeing] = useState<AICTEAgeingResponse | null>(null);
  const [sla, setSla] = useState<AICTESLAResponse | null>(null);
  const [trends, setTrends] = useState<AICTETrendsResponse | null>(null);
  const [unitsData, setUnitsData] = useState<AICTEOrganizationalUnitsAnalyticsResponse | null>(null);
  const [institutionsData, setInstitutionsData] = useState<AICTEInstitutionsAnalyticsResponse | null>(null);
  const [transferData, setTransferData] = useState<AICTETransferAnalyticsResponse | null>(null);
  const [crossBureauData, setCrossBureauData] = useState<AICTECrossBureauAnalyticsResponse | null>(null);
  
  // Units for dropdown filter
  const [availableUnits, setAvailableUnits] = useState<{ id: number; code: string; name: string }[]>([]);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<string>('');

  // Modals
  const [isIntakeOpen, setIsIntakeOpen] = useState(false);
  const [isReferOpen, setIsReferOpen] = useState(false);

  useEffect(() => {
    fetchAvailableUnits();
  }, []);

  useEffect(() => {
    fetchDashboardAnalytics();
  }, [periodPreset, selectedUnitId, selectedRegion]);

  const fetchAvailableUnits = async () => {
    try {
      const res = await api.get<{ units: { id: number; code: string; name: string }[] }>('/aicte/organizational-units');
      setAvailableUnits(res.units || []);
    } catch {
      // Ignore
    }
  };

  const getDateRangeParams = () => {
    if (periodPreset === 'all') return {};
    const now = new Date();
    const days = periodPreset === '30d' ? 30 : periodPreset === '90d' ? 90 : 180;
    const from = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
    return {
      from_date: from.toISOString(),
      to_date: now.toISOString(),
    };
  };

  const fetchDashboardAnalytics = async () => {
    setLoading(true);
    try {
      const dateParams = getDateRangeParams();
      const queryParams = new URLSearchParams();
      if (dateParams.from_date) queryParams.set('from_date', dateParams.from_date);
      if (dateParams.to_date) queryParams.set('to_date', dateParams.to_date);
      if (selectedUnitId) queryParams.set('organizational_unit_id', selectedUnitId);
      if (selectedRegion) queryParams.set('region', selectedRegion);

      const qs = queryParams.toString() ? `?${queryParams.toString()}` : '';

      const [
        overviewRes,
        ageingRes,
        slaRes,
        trendsRes,
        unitsRes,
        instsRes,
        transfersRes,
        crossRes,
      ] = await Promise.all([
        api.get<AICTEOverviewAnalyticsResponse>(`/aicte/analytics/overview${qs}`).catch(() => null),
        api.get<AICTEAgeingResponse>(`/aicte/analytics/ageing${qs}`).catch(() => null),
        api.get<AICTESLAResponse>(`/aicte/analytics/sla${qs}`).catch(() => null),
        api.get<AICTETrendsResponse>(`/aicte/analytics/trends?months_back=6${selectedUnitId ? `&organizational_unit_id=${selectedUnitId}` : ''}`).catch(() => null),
        api.get<AICTEOrganizationalUnitsAnalyticsResponse>(`/aicte/analytics/organizational-units${qs}`).catch(() => null),
        api.get<AICTEInstitutionsAnalyticsResponse>(`/aicte/analytics/institutions${qs}&limit=10`).catch(() => null),
        api.get<AICTETransferAnalyticsResponse>(`/aicte/analytics/transfers${qs}`).catch(() => null),
        api.get<AICTECrossBureauAnalyticsResponse>('/aicte/analytics/cross-bureau').catch(() => null),
      ]);

      setOverview(overviewRes);
      setAgeing(ageingRes);
      setSla(slaRes);
      setTrends(trendsRes);
      setUnitsData(unitsRes);
      setInstitutionsData(instsRes);
      setTransferData(transfersRes);
      setCrossBureauData(crossRes);
      setLastRefreshedAt(new Date().toLocaleTimeString());
    } catch {
      // Keep existing data
    } finally {
      setLoading(false);
    }
  };

  const handleExportCasesCsv = () => {
    const dateParams = getDateRangeParams();
    const queryParams = new URLSearchParams();
    if (dateParams.from_date) queryParams.set('from_date', dateParams.from_date);
    if (dateParams.to_date) queryParams.set('to_date', dateParams.to_date);
    if (selectedUnitId) queryParams.set('organizational_unit_id', selectedUnitId);
    if (selectedRegion) queryParams.set('region', selectedRegion);
    const qs = queryParams.toString() ? `?${queryParams.toString()}` : '';
    window.open(`/api/v1/aicte/analytics/reports/cases.csv${qs}`, '_blank');
  };

  const handleExportSummaryCsv = () => {
    const dateParams = getDateRangeParams();
    const queryParams = new URLSearchParams();
    if (dateParams.from_date) queryParams.set('from_date', dateParams.from_date);
    if (dateParams.to_date) queryParams.set('to_date', dateParams.to_date);
    const qs = queryParams.toString() ? `?${queryParams.toString()}` : '';
    window.open(`/api/v1/aicte/analytics/reports/summary.csv${qs}`, '_blank');
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
                AICTE Integrated Case Monitoring & Analytics Dashboard
              </h1>
              <p className="text-xs text-slate-500">
                Data-driven regulatory oversight, ageing distribution, SLA compliance, and cross-bureau tracking
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={fetchDashboardAnalytics}
            disabled={loading}
            className="p-2 border border-slate-200 rounded-xl hover:bg-slate-50 text-slate-600 transition text-xs flex items-center gap-1.5 shadow-sm bg-white"
            title="Refresh dashboard"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-600' : ''}`} />
            Refresh
          </button>

          <Link
            to="/aicte/transfers"
            className="flex items-center gap-1.5 px-3.5 py-2 border border-slate-200 text-slate-700 bg-white text-xs font-semibold rounded-xl hover:bg-slate-50 transition shadow-sm"
          >
            <ArrowRightLeft className="w-4 h-4 text-purple-600" />
            Transfers {overview && overview.pending_transfers_count > 0 && (
              <span className="bg-purple-100 text-purple-800 text-[10px] px-1.5 py-0.2 rounded-full font-bold">
                {overview.pending_transfers_count}
              </span>
            )}
          </Link>

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
            Direct Intake
          </button>

          {/* Export Dropdown / Actions */}
          <div className="flex items-center gap-1.5">
            <button
              onClick={handleExportCasesCsv}
              className="flex items-center gap-1.5 px-3 py-2 border border-slate-200 text-slate-700 bg-white text-xs font-semibold rounded-xl hover:bg-slate-50 transition shadow-sm"
              title="Export filtered case records to CSV"
            >
              <Download className="w-3.5 h-3.5 text-slate-500" />
              Cases CSV
            </button>
            <button
              onClick={handleExportSummaryCsv}
              className="flex items-center gap-1.5 px-3 py-2 border border-slate-200 text-slate-700 bg-white text-xs font-semibold rounded-xl hover:bg-slate-50 transition shadow-sm"
              title="Export high-level summary KPIs to CSV"
            >
              <Download className="w-3.5 h-3.5 text-emerald-600" />
              Summary CSV
            </button>
          </div>
        </div>
      </div>

      {/* Analytics Controls & Filters Bar */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 mr-1">
            <Filter className="w-3.5 h-3.5 text-blue-600" />
            Filters:
          </div>

          {/* Period presets */}
          <div className="inline-flex rounded-xl border border-slate-200 p-0.5 bg-slate-50 text-xs font-medium">
            <button
              onClick={() => setPeriodPreset('all')}
              className={`px-3 py-1 rounded-lg transition ${
                periodPreset === 'all' ? 'bg-white text-blue-700 font-semibold shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All Time
            </button>
            <button
              onClick={() => setPeriodPreset('30d')}
              className={`px-3 py-1 rounded-lg transition ${
                periodPreset === '30d' ? 'bg-white text-blue-700 font-semibold shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Last 30 Days
            </button>
            <button
              onClick={() => setPeriodPreset('90d')}
              className={`px-3 py-1 rounded-lg transition ${
                periodPreset === '90d' ? 'bg-white text-blue-700 font-semibold shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Last 90 Days
            </button>
            <button
              onClick={() => setPeriodPreset('180d')}
              className={`px-3 py-1 rounded-lg transition ${
                periodPreset === '180d' ? 'bg-white text-blue-700 font-semibold shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Last 6 Months
            </button>
          </div>

          {/* Bureau Unit Filter */}
          <select
            value={selectedUnitId}
            onChange={(e) => setSelectedUnitId(e.target.value)}
            className="text-xs border border-slate-200 rounded-xl px-3 py-1.5 bg-white text-slate-700 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20"
          >
            <option value="">All Bureaus / Units</option>
            {availableUnits.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name} ({u.code})
              </option>
            ))}
          </select>

          {/* Region Filter */}
          <select
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
            className="text-xs border border-slate-200 rounded-xl px-3 py-1.5 bg-white text-slate-700 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20"
          >
            <option value="">All Regions</option>
            <option value="Northern">Northern Region</option>
            <option value="Western">Western Region</option>
            <option value="Southern">Southern Region</option>
            <option value="Eastern">Eastern Region</option>
            <option value="Central">Central Region</option>
            <option value="North-West">North-West Region</option>
            <option value="South-West">South-West Region</option>
          </select>
        </div>

        {lastRefreshedAt && (
          <div className="text-[11px] text-slate-400 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            Last updated: {lastRefreshedAt}
          </div>
        )}
      </div>

      {/* KPI Overview Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Received */}
        <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Received</span>
            <Activity className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-3xl font-bold text-slate-900 mt-2">{overview?.total_received ?? 0}</p>
          <div className="flex items-center gap-1 mt-1 text-[11px] text-slate-500">
            <span>{overview?.total_active ?? 0} active backlog</span>
          </div>
        </div>

        {/* Overdue Next Actions */}
        <Link
          to="/aicte/cases"
          className="p-5 bg-white border border-rose-200/80 rounded-2xl shadow-sm hover:border-rose-300 transition group block"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-rose-600 uppercase tracking-wider">Overdue Actions</span>
            <AlertTriangle className="w-4 h-4 text-rose-600 group-hover:scale-110 transition" />
          </div>
          <p className="text-3xl font-bold text-rose-700 mt-2">{overview?.overdue_actions_count ?? 0}</p>
          <p className="text-[11px] text-rose-500 mt-1">Next action deadline breached</p>
        </Link>

        {/* Overdue Expected Disposal */}
        <div className="p-5 bg-white border border-amber-200/80 rounded-2xl shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-600 uppercase tracking-wider">Overdue Disposal</span>
            <Clock className="w-4 h-4 text-amber-600" />
          </div>
          <p className="text-3xl font-bold text-amber-700 mt-2">{overview?.overdue_disposal_count ?? 0}</p>
          <p className="text-[11px] text-slate-400 mt-1">Past expected disposal target</p>
        </div>

        {/* Disposed Cases & Rate */}
        <div className="p-5 bg-white border border-emerald-200/80 rounded-2xl shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider">Disposed Orders</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="flex items-baseline gap-2 mt-2">
            <p className="text-3xl font-bold text-emerald-700">{overview?.total_disposed ?? 0}</p>
            {overview?.disposal_rate !== null && overview?.disposal_rate !== undefined && (
              <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded-md">
                {overview.disposal_rate}%
              </span>
            )}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Regulatory orders dispatched</p>
        </div>

        {/* Overlap & Transfer Alert */}
        <Link
          to="/aicte/overlaps"
          className="p-5 bg-gradient-to-br from-indigo-50/70 to-blue-50/60 border border-blue-200 rounded-2xl shadow-sm hover:shadow transition group block"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-indigo-700 uppercase tracking-wider">Coordination</span>
            <ArrowRightLeft className="w-4 h-4 text-indigo-600 group-hover:translate-x-0.5 transition" />
          </div>
          <p className="text-3xl font-bold text-indigo-900 mt-2">{overview?.pending_overlaps_count ?? 0}</p>
          <div className="flex items-center justify-between mt-1 text-[11px] text-indigo-600">
            <span>Pending overlap alerts</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </div>
        </Link>
      </div>

      {/* Row 2: Visual Charts - Ageing Analysis & Workload Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Case Ageing Distribution Chart */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-blue-600" />
                Active Case Ageing Backlog Distribution
              </h2>
              <p className="text-xs text-slate-500">
                Days elapsed since case receipt for active, non-disposed dockets
              </p>
            </div>
            {ageing?.average_active_age_days !== undefined && (
              <div className="text-right">
                <span className="text-[11px] text-slate-400 block">Avg Backlog Age</span>
                <span className="text-xs font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded">
                  {ageing.average_active_age_days} days
                </span>
              </div>
            )}
          </div>

          {ageing && ageing.buckets.length > 0 ? (
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={ageing.buckets} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="bg-slate-900 text-white p-2.5 rounded-xl text-xs shadow-lg space-y-1">
                            <p className="font-bold">{data.label}</p>
                            <p className="text-slate-300">Cases: <span className="font-semibold text-white">{data.count}</span></p>
                            <p className="text-slate-300">Share: <span className="font-semibold text-emerald-400">{data.percentage}%</span></p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {ageing.buckets.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={AGE_COLORS[index % AGE_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-slate-400 text-xs">
              No active cases to display in ageing analysis.
            </div>
          )}

          <div className="grid grid-cols-5 gap-2 pt-2 border-t border-slate-100 text-center">
            {ageing?.buckets.map((b, idx) => (
              <div key={b.bucket_key} className="p-1.5 rounded-lg bg-slate-50">
                <span className="text-[10px] text-slate-500 font-medium block truncate">{b.label}</span>
                <span className="text-xs font-bold text-slate-800">{b.count}</span>
                <span className="text-[10px] text-slate-400 block">({b.percentage}%)</span>
              </div>
            ))}
          </div>
        </div>

        {/* 6-Month Chronological Workload Trends */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4 text-emerald-600" />
                Workload & Disposal Trends (Last 6 Months)
              </h2>
              <p className="text-xs text-slate-500">
                Monthly cases received, formal regulatory orders, and accepted transfers
              </p>
            </div>
          </div>

          {trends && trends.trend_points.length > 0 ? (
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trends.trend_points} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorReceived" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorDisposed" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="period" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="bg-slate-900 text-white p-2.5 rounded-xl text-xs shadow-lg space-y-1">
                            <p className="font-bold text-slate-200">{data.period}</p>
                            <p className="text-blue-400">Received: <span className="font-bold text-white">{data.received_count}</span></p>
                            <p className="text-emerald-400">Disposed: <span className="font-bold text-white">{data.disposed_count}</span></p>
                            <p className="text-orange-400">Transferred: <span className="font-bold text-white">{data.transferred_count}</span></p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: 11 }} />
                  <Area type="monotone" dataKey="received_count" name="Cases Received" stroke="#3b82f6" fillOpacity={1} fill="url(#colorReceived)" strokeWidth={2} />
                  <Area type="monotone" dataKey="disposed_count" name="Disposed Orders" stroke="#10b981" fillOpacity={1} fill="url(#colorDisposed)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-slate-400 text-xs">
              No trend records available for the selected period.
            </div>
          )}

          <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
            <span>Tracking monthly case intake vs disposals</span>
            <span className="font-medium text-slate-700">6 Continuous Period Buckets</span>
          </div>
        </div>
      </div>

      {/* Row 3: SLA Performance & Status Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* SLA Timeliness & Deadlines Card */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4 text-rose-600" />
            SLA & Timeliness Compliance
          </h2>
          <p className="text-xs text-slate-500">
            Citizen Charter benchmarks and statutory action deadlines
          </p>

          <div className="space-y-2.5 pt-2">
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50">
              <div>
                <span className="text-xs font-semibold text-slate-700 block">SLA Compliance Rate</span>
                <span className="text-[11px] text-slate-400">Cases adhering to target deadlines</span>
              </div>
              <span className="text-lg font-bold text-emerald-600">
                {sla?.sla_compliance_rate !== null && sla?.sla_compliance_rate !== undefined ? `${sla.sla_compliance_rate}%` : 'N/A'}
              </span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-xl border border-rose-100 bg-rose-50/50">
              <span className="text-xs text-rose-800">Overdue Next Action</span>
              <span className="text-xs font-bold text-rose-700">{sla?.overdue_next_action_count ?? 0}</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-xl border border-amber-100 bg-amber-50/50">
              <span className="text-xs text-amber-800">Overdue Expected Disposal</span>
              <span className="text-xs font-bold text-amber-700">{sla?.overdue_expected_disposal_count ?? 0}</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-xl border border-slate-200 bg-slate-50/60">
              <span className="text-xs text-slate-600">Escalated Priority Dockets</span>
              <span className="text-xs font-bold text-slate-800">{sla?.escalated_cases_count ?? 0}</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-xl border border-slate-100 bg-white">
              <span className="text-xs text-slate-500">Missing Next Action Deadline</span>
              <span className="text-xs font-semibold text-slate-600">{sla?.missing_next_action_deadline_count ?? 0}</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-xl border border-slate-100 bg-white">
              <span className="text-xs text-slate-500">Missing Expected Disposal Target</span>
              <span className="text-xs font-semibold text-slate-600">{sla?.missing_expected_disposal_count ?? 0}</span>
            </div>
          </div>
        </div>

        {/* Status Distribution Pie / Breakdown */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3 lg:col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-blue-600" />
              Comprehensive Lifecycle Status Distribution
            </h2>
            <Link to="/aicte/cases" className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1">
              View All Cases <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <p className="text-xs text-slate-500">
            Real-time count of cases across all 10 procedural state-machine statuses
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2">
            {overview?.status_distribution.map((s) => (
              <Link
                key={s.status}
                to={`/aicte/cases?status=${s.status}`}
                className="p-2.5 rounded-xl border border-slate-100 hover:border-blue-200 hover:bg-blue-50/30 transition text-left block"
              >
                <div className="flex items-center gap-1.5 mb-1">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: STATUS_COLORS[s.status] || '#94a3b8' }}
                  />
                  <span className="text-[11px] font-medium text-slate-600 truncate">{s.label}</span>
                </div>
                <span className="text-lg font-bold text-slate-900">{s.count}</span>
              </Link>
            ))}
          </div>

          {/* Transfer & Overlap Highlights */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-3 border-t border-slate-100">
            <div className="p-3 bg-purple-50/60 border border-purple-100 rounded-xl flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-purple-900 block">Inter-Bureau Transfers</span>
                <span className="text-[11px] text-purple-600">
                  {transferData?.accepted_count ?? 0} Accepted · {transferData?.pending_acceptance_count ?? 0} Awaiting Acceptance
                </span>
              </div>
              <Link
                to="/aicte/transfers"
                className="text-xs font-bold text-purple-700 bg-white border border-purple-200 px-2.5 py-1 rounded-lg hover:bg-purple-100 transition shadow-2xs"
              >
                Queue
              </Link>
            </div>

            <div className="p-3 bg-blue-50/60 border border-blue-100 rounded-xl flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-blue-900 block">Cross-Bureau Coordination</span>
                <span className="text-[11px] text-blue-600">
                  {crossBureauData?.confirmed_related ?? 0} Linked · {crossBureauData?.pending_review_overlaps ?? 0} Pending Review
                </span>
              </div>
              <Link
                to="/aicte/overlaps"
                className="text-xs font-bold text-blue-700 bg-white border border-blue-200 px-2.5 py-1 rounded-lg hover:bg-blue-100 transition shadow-2xs"
              >
                Overlaps
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Row 4: Bureau Workload & Regional Distribution Table */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
              <Building2 className="w-4 h-4 text-purple-600" />
              Bureau, Cell, and Regional Office Workload Breakdown
            </h2>
            <p className="text-xs text-slate-500">
              Active caseload, overdue dockets, and pending incoming transfers by organizational unit
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 font-semibold bg-slate-50/50">
                <th className="py-2.5 px-3">Unit Name</th>
                <th className="py-2.5 px-3">Code</th>
                <th className="py-2.5 px-3">Type</th>
                <th className="py-2.5 px-3 text-right">Total Cases</th>
                <th className="py-2.5 px-3 text-right">Active Backlog</th>
                <th className="py-2.5 px-3 text-right">Overdue</th>
                <th className="py-2.5 px-3 text-right">Disposed</th>
                <th className="py-2.5 px-3 text-right">Incoming Transfers</th>
                <th className="py-2.5 px-3 text-right">Disposal Rate</th>
                <th className="py-2.5 px-3 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {unitsData && unitsData.units.length > 0 ? (
                unitsData.units.map((u) => (
                  <tr key={u.unit_id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3 px-3 font-semibold text-slate-900">{u.name}</td>
                    <td className="py-3 px-3">
                      <span className="font-mono bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded text-[11px]">
                        {u.code}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-500">{u.unit_type}</td>
                    <td className="py-3 px-3 text-right font-medium">{u.total_cases}</td>
                    <td className="py-3 px-3 text-right font-bold text-blue-600">{u.active_cases}</td>
                    <td className="py-3 px-3 text-right">
                      {u.overdue_cases > 0 ? (
                        <span className="text-rose-600 font-bold bg-rose-50 px-1.5 py-0.5 rounded">
                          {u.overdue_cases}
                        </span>
                      ) : (
                        <span className="text-slate-400">0</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-right text-emerald-600 font-medium">{u.disposed_cases}</td>
                    <td className="py-3 px-3 text-right">
                      {u.pending_incoming_transfers > 0 ? (
                        <span className="text-purple-700 font-bold bg-purple-50 px-1.5 py-0.5 rounded">
                          {u.pending_incoming_transfers}
                        </span>
                      ) : (
                        <span className="text-slate-400">0</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-right font-medium">
                      {u.disposal_rate !== null ? `${u.disposal_rate}%` : 'N/A'}
                    </td>
                    <td className="py-3 px-3 text-center">
                      <Link
                        to={`/aicte/cases?unit_id=${u.unit_id}`}
                        className="text-[11px] font-semibold text-blue-600 hover:text-blue-800 underline"
                      >
                        View Cases
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={10} className="py-6 text-center text-slate-400">
                    No organizational unit records found matching current scope.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Row 5: Top Institutions by Case Load */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
              <Building2 className="w-4 h-4 text-blue-600" />
              Institutions with Highest Case Volume
            </h2>
            <p className="text-xs text-slate-500">
              Aggregated complaints across all AICTE Bureaus, sorted by total case history
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 font-semibold bg-slate-50/50">
                <th className="py-2.5 px-3">Institution Name</th>
                <th className="py-2.5 px-3">AICTE Permanent ID</th>
                <th className="py-2.5 px-3">State / Region</th>
                <th className="py-2.5 px-3 text-right">Total Cases</th>
                <th className="py-2.5 px-3 text-right">Active Cases</th>
                <th className="py-2.5 px-3 text-right">Overdue</th>
                <th className="py-2.5 px-3 text-right">Disposed</th>
                <th className="py-2.5 px-3 text-right">Disposal Rate</th>
                <th className="py-2.5 px-3 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {institutionsData && institutionsData.institutions.length > 0 ? (
                institutionsData.institutions.map((inst) => (
                  <tr key={inst.institution_id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3 px-3 font-semibold text-slate-900">{inst.name}</td>
                    <td className="py-3 px-3 font-mono text-[11px] text-slate-600">
                      {inst.aicte_permanent_id || 'Not Verified'}
                    </td>
                    <td className="py-3 px-3 text-slate-500">
                      {inst.state || '-'} {inst.region ? `(${inst.region})` : ''}
                    </td>
                    <td className="py-3 px-3 text-right font-medium">{inst.total_cases}</td>
                    <td className="py-3 px-3 text-right font-bold text-blue-600">{inst.active_cases}</td>
                    <td className="py-3 px-3 text-right">
                      {inst.overdue_cases > 0 ? (
                        <span className="text-rose-600 font-bold bg-rose-50 px-1.5 py-0.5 rounded">
                          {inst.overdue_cases}
                        </span>
                      ) : (
                        <span className="text-slate-400">0</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-right text-emerald-600 font-medium">{inst.disposed_cases}</td>
                    <td className="py-3 px-3 text-right font-medium">
                      {inst.disposal_rate !== null ? `${inst.disposal_rate}%` : 'N/A'}
                    </td>
                    <td className="py-3 px-3 text-center">
                      <Link
                        to={`/aicte/institutions/${inst.institution_id}`}
                        className="text-[11px] font-semibold text-blue-600 hover:text-blue-800 underline"
                      >
                        Unified Profile
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={9} className="py-6 text-center text-slate-400">
                    No institution records found for the selected filter parameters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modals */}
      {isIntakeOpen && (
        <CreateAICTECaseModal
          isOpen={isIntakeOpen}
          onClose={() => setIsIntakeOpen(false)}
          onSuccess={() => {
            setIsIntakeOpen(false);
            fetchDashboardAnalytics();
          }}
        />
      )}

      {isReferOpen && (
        <ReferGrievanceModal
          isOpen={isReferOpen}
          onClose={() => setIsReferOpen(false)}
          onSuccess={() => {
            setIsReferOpen(false);
            fetchDashboardAnalytics();
          }}
        />
      )}
    </div>
  );
};
