import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../services/api';
import { Grievance, DashboardStats } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { PriorityBadge } from '../../components/common/PriorityBadge';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';
import { 
  PlusCircle, 
  Search, 
  FileText, 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  ArrowRight,
  Filter,
  Eye
} from 'lucide-react';

export const StudentDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [grievances, setGrievances] = useState<Grievance[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  useEffect(() => {
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
        console.error('Failed to load student dashboard', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const filteredGrievances = grievances.filter((g) => {
    const matchesSearch = 
      g.title.toLowerCase().includes(search.toLowerCase()) ||
      g.reference_number.toLowerCase().includes(search.toLowerCase()) ||
      g.category_name.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || g.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return <LoadingSpinner message="Loading your grievance dashboard..." />;
  }

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900">
            Welcome back, {user?.full_name}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Track your submissions, communicate with grievance officers, and view real-time resolution updates.
          </p>
        </div>
        <Link
          to="/student/submit"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition shadow-sm shrink-0"
        >
          <PlusCircle className="w-4 h-4" />
          Submit New Grievance
        </Link>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Filed</span>
            <FileText className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-2xl font-extrabold text-slate-900">{stats?.total_grievances || 0}</p>
          <p className="text-[11px] text-slate-400 mt-1">Active institutional record</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pending Action</span>
            <Clock className="w-4 h-4 text-amber-500" />
          </div>
          <p className="text-2xl font-extrabold text-amber-600">{stats?.pending_grievances || 0}</p>
          <p className="text-[11px] text-slate-400 mt-1">Under officer triage</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">In Progress</span>
            <AlertCircle className="w-4 h-4 text-indigo-600" />
          </div>
          <p className="text-2xl font-extrabold text-indigo-600">{stats?.in_investigation_grievances || 0}</p>
          <p className="text-[11px] text-slate-400 mt-1">Inquiry in progress</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Resolved</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-2xl font-extrabold text-emerald-600">{stats?.resolved_grievances || 0}</p>
          <p className="text-[11px] text-slate-400 mt-1">Closed or verified</p>
        </div>
      </div>

      {/* Grievances List Container */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        {/* Search & Filter Header */}
        <div className="p-4 sm:p-5 border-b border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by title or reference..."
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
              <option value="SUBMITTED">Submitted</option>
              <option value="UNDER_REVIEW">Under Review</option>
              <option value="INVESTIGATION_IN_PROGRESS">Investigating</option>
              <option value="RESOLUTION_PROPOSED">Resolution Proposed</option>
              <option value="RESOLVED">Resolved</option>
              <option value="ESCALATED">Escalated</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>
        </div>

        {/* Table or Empty State */}
        {filteredGrievances.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No grievances found"
              description="You have not submitted any grievances matching the search filter."
              action={{
                label: 'Submit Your First Grievance',
                onClick: () => navigate('/student/submit'),
              }}
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/70 border-b border-slate-100 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Reference</th>
                  <th className="py-3 px-4">Title & Category</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4">Submitted</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {filteredGrievances.map((g) => (
                  <tr key={g.id} className="hover:bg-slate-50/60 transition group">
                    <td className="py-3.5 px-4 font-mono font-semibold text-slate-900">
                      {g.reference_number}
                    </td>
                    <td className="py-3.5 px-4 max-w-xs sm:max-w-md">
                      <p className="font-semibold text-slate-900 truncate">{g.title}</p>
                      <span className="text-[11px] text-slate-400">{g.category_name}</span>
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <StatusBadge status={g.status} />
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <PriorityBadge priority={g.priority} />
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap text-slate-500">
                      {new Date(g.created_at).toLocaleDateString('en-IN', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                      })}
                    </td>
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <Link
                        to={`/student/grievances/${g.id}`}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-slate-700 hover:text-blue-600 hover:border-blue-200 text-xs font-medium transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        Details
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
