import React, { useState } from 'react';
import { Search, ShieldAlert, CheckCircle2, Clock, AlertTriangle, ArrowRight } from 'lucide-react';
import { StatusBadge } from '../../components/common/StatusBadge';
import { GrievanceStatus } from '../../types';

import { api } from '../../services/api';

export const TrackGrievancePage: React.FC = () => {
  const [refNumber, setRefNumber] = useState('');
  const [studentIdLast4, setStudentIdLast4] = useState('');
  const [hasSearched, setHasSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    reference: string;
    institution: string;
    category: string;
    status: GrievanceStatus;
    submittedDate: string;
    lastUpdated: string;
    title: string;
    resolutionSummary?: string;
    statusHistory: Array<{
      id: number;
      from_status: string | null;
      to_status: string;
      changed_by_name: string;
      reason?: string;
      created_at: string;
    }>;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleTrack = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const cleanRef = refNumber.trim().toUpperCase();
    if (!cleanRef) return;

    setLoading(true);
    setHasSearched(true);

    try {
      const data = await api.get<{
        reference_number: string;
        institution_name: string;
        category_name: string;
        status: GrievanceStatus;
        title: string;
        created_at: string;
        updated_at: string;
        resolution_summary?: string;
        status_history?: Array<{
          id: number;
          from_status: string | null;
          to_status: string;
          changed_by_name: string;
          reason?: string;
          created_at: string;
        }>;
      }>(`/grievances/track/${encodeURIComponent(cleanRef)}`);

      setResult({
        reference: data.reference_number,
        institution: data.institution_name,
        category: data.category_name,
        status: data.status,
        title: data.title,
        submittedDate: new Date(data.created_at).toLocaleDateString(),
        lastUpdated: new Date(data.updated_at).toLocaleDateString(),
        resolutionSummary: data.resolution_summary,
        statusHistory: data.status_history || [],
      });
    } catch (err: any) {
      setError(err.message || 'No grievance record found matching this Reference Number.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-16">
      <div className="text-center mb-10">
        <div className="w-12 h-12 rounded-2xl bg-blue-100 text-blue-600 flex items-center justify-center mx-auto mb-4">
          <Search className="w-6 h-6" />
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900">Track Grievance Status</h1>
        <p className="mt-2 text-sm text-slate-500">
          Enter your official reference number to view progress milestones and verified resolution records.
        </p>
      </div>

      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200/80 shadow-sm">
        <form onSubmit={handleTrack} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Grievance Reference Number *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. GRV-2026-EXAM01"
              value={refNumber}
              onChange={(e) => setRefNumber(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-mono uppercase"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm transition shadow-sm flex items-center justify-center gap-2"
          >
            {loading ? 'Verifying Registry...' : 'Check Status Milestones'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {error && (
          <div className="mt-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            {error}
          </div>
        )}

        {result && (
          <div className="mt-8 pt-8 border-t border-slate-100 animate-in fade-in duration-200 space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-slate-400">Public Reference</p>
                <p className="text-base font-bold text-slate-800 font-mono">{result.reference}</p>
              </div>
              <StatusBadge status={result.status} />
            </div>

            <div className="grid grid-cols-2 gap-4 text-xs bg-slate-50 p-4 rounded-xl border border-slate-100">
              <div>
                <span className="text-slate-400 block mb-0.5">Institution:</span>
                <span className="font-semibold text-slate-800">{result.institution}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-0.5">Category:</span>
                <span className="font-semibold text-slate-800">{result.category}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-0.5">Date Submitted:</span>
                <span className="font-medium text-slate-700">{result.submittedDate}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-0.5">Last Activity:</span>
                <span className="font-medium text-slate-700">{result.lastUpdated}</span>
              </div>
            </div>

            {result.resolutionSummary && (
              <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-900">
                <span className="font-bold block mb-1">Official Resolution Summary:</span>
                <p className="leading-relaxed">{result.resolutionSummary}</p>
              </div>
            )}

            {result.statusHistory.length > 0 && (
              <div className="space-y-3 pt-2">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Verified Audit Timeline
                </h4>
                <div className="space-y-2 border-l-2 border-slate-200 pl-3">
                  {result.statusHistory.map((h) => (
                    <div key={h.id} className="text-xs space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-800">{h.to_status.replace('_', ' ')}</span>
                        <span className="text-[10px] text-slate-400 font-mono">
                          {new Date(h.created_at).toLocaleString()}
                        </span>
                      </div>
                      {h.reason && <p className="text-slate-500 text-[11px] italic">"{h.reason}"</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <p className="text-[11px] text-slate-400 mt-4 text-center">
              Confidential complaint details, student identity, and internal officer communications are shielded in public tracking.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
