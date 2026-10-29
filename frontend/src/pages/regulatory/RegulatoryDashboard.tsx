import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../services/api';
import { Institution, DashboardStats, Grievance } from '../../types';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { StatusBadge } from '../../components/common/StatusBadge';
import { 
  ShieldCheck, 
  Building2, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  MapPin, 
  BarChart3,
  Search,
  FileSpreadsheet
} from 'lucide-react';

export const RegulatoryDashboard: React.FC = () => {
  const { user } = useAuth();

  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [selectedState, setSelectedState] = useState<string>('Delhi');
  const [loading, setLoading] = useState(true);
  const [exportingCSV, setExportingCSV] = useState(false);

  useEffect(() => {
    const fetchRegulatoryData = async () => {
      try {
        setLoading(true);
        const [instList, statsData] = await Promise.all([
          api.get<Institution[]>('/institutions'),
          api.get<DashboardStats>('/analytics/dashboard')
        ]);
        setInstitutions(instList);
        setStats(statsData);
      } catch (err) {
        console.error('Failed to load regulatory data', err);
      } finally {
        setLoading(false);
      }
    };
    fetchRegulatoryData();
  }, []);

  const handleExportCSV = async () => {
    setExportingCSV(true);
    try {
      await api.downloadFile('/analytics/export/csv', 'jurisdiction_compliance_report.csv');
    } catch (err: any) {
      alert(err.message || 'Failed to download compliance report.');
    } finally {
      setExportingCSV(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Validating jurisdictional access & institution registry..." />;
  }

  const calculatedRate = stats && stats.total_grievances > 0 
    ? Math.round((stats.resolved_grievances / stats.total_grievances) * 100)
    : (stats?.satisfaction_rate || 0);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200 uppercase tracking-wide">
            Regional Regulatory Oversight Council
          </span>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 mt-2">
            Jurisdiction Compliance & Monitoring Portal
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Monitoring higher education institutions across assigned regional jurisdictions.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-slate-400" />
            <span className="text-xs font-semibold text-slate-700">Assigned State:</span>
            <span className="text-xs font-bold px-3 py-1 rounded-lg bg-blue-50 text-blue-700 border border-blue-200">
              Delhi Region (Active)
            </span>
          </div>

          <button
            onClick={handleExportCSV}
            disabled={exportingCSV}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs transition shadow-sm disabled:opacity-50"
          >
            <FileSpreadsheet className="w-4 h-4" />
            {exportingCSV ? 'Downloading...' : 'Export Compliance CSV'}
          </button>
        </div>
      </div>

      {/* Aggregate Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Affiliated Colleges</span>
          <p className="text-2xl font-extrabold text-slate-900">{institutions.length}</p>
          <span className="text-[11px] text-slate-400">Within monitored jurisdiction</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Regional Grievances</span>
          <p className="text-2xl font-extrabold text-blue-600">{stats?.total_grievances || 0}</p>
          <span className="text-[11px] text-slate-400">Centralized filings</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Overdue Breaches</span>
          <p className="text-2xl font-extrabold text-rose-600">{stats?.overdue_grievances || 0}</p>
          <span className="text-[11px] text-rose-500 font-medium">Compliance escalation flag</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Regional Resolution Rate</span>
          <p className="text-2xl font-extrabold text-emerald-600">{calculatedRate}%</p>
          <span className="text-[11px] text-emerald-600 font-medium">Institutional benchmark</span>
        </div>
      </div>

      {/* Institution Benchmark Comparison Cards */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="font-bold text-slate-900 text-sm">Monitored Institutional Performance</h3>
            <p className="text-xs text-slate-500 mt-0.5">Comparative overview of grievance cells under your regulatory scope.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {institutions.map((inst) => (
            <div key={inst.id} className="p-5 rounded-2xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:shadow-md transition">
              <div className="flex items-start justify-between mb-3">
                <div className="w-9 h-9 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-sm">
                  <Building2 className="w-5 h-5" />
                </div>
                <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                  <CheckCircle2 className="w-3 h-3" /> Verified Cell
                </span>
              </div>

              <h4 className="font-bold text-slate-900 text-sm mb-1 leading-snug">{inst.name}</h4>
              <p className="text-xs font-mono text-slate-400 mb-3">{inst.code} • {inst.city}, {inst.state}</p>

              <div className="space-y-1.5 text-xs text-slate-600 border-t border-slate-200 pt-3">
                <div className="flex justify-between">
                  <span className="text-slate-400">Resolution Rate:</span>
                  <span className="font-semibold text-slate-800">92%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Avg Resolution:</span>
                  <span className="font-semibold text-slate-800">4.5 Days</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Contact Officer:</span>
                  <span className="font-semibold text-slate-800 truncate">{inst.contact_email}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
