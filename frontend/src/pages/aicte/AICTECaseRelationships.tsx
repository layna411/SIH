import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AICTECaseLink, AICTECaseLinkType, ManualLinkCreatePayload } from '../../types';
import { api } from '../../services/api';
import { 
  Link as LinkIcon, 
  Search, 
  Plus, 
  CheckCircle, 
  AlertCircle, 
  RefreshCw, 
  ExternalLink, 
  ShieldAlert,
  X,
  Layers
} from 'lucide-react';

interface AICTECaseRelationshipsProps {
  caseId: number;
  caseReference: string;
}

export const AICTECaseRelationships: React.FC<AICTECaseRelationshipsProps> = ({
  caseId,
  caseReference,
}) => {
  const [links, setLinks] = useState<AICTECaseLink[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Scan state
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<string | null>(null);

  // Manual link modal state
  const [isManualModalOpen, setIsManualModalOpen] = useState(false);
  const [targetCaseId, setTargetCaseId] = useState('');
  const [linkType, setLinkType] = useState<AICTECaseLinkType>('RELATED_TO');
  const [linkNotes, setLinkNotes] = useState('');
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  useEffect(() => {
    loadLinks();
  }, [caseId]);

  const loadLinks = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<AICTECaseLink[]>(`/aicte/overlaps/cases/${caseId}/links`);
      setLinks(data || []);
    } catch (err: any) {
      setError(err?.message || 'Failed to load case relationships.');
    } finally {
      setLoading(false);
    }
  };

  const handleScanOverlaps = async () => {
    setScanning(true);
    setScanResult(null);
    try {
      const res = await api.post<{
        status: string;
        case_id: number;
        scanned_candidates_count: number;
        created_candidates_count: number;
        candidates: any[];
      }>(`/aicte/overlaps/detect/${caseId}`);

      if (res.created_candidates_count > 0) {
        setScanResult(`Detection complete: ${res.created_candidates_count} new candidate pair(s) flagged for human review.`);
      } else if (res.scanned_candidates_count > 0) {
        setScanResult(`Scanned ${res.scanned_candidates_count} eligible institutional cases. No new candidate overlaps detected.`);
      } else {
        setScanResult('No other institutional cases found in the database to compare against.');
      }
    } catch (err: any) {
      setScanResult(`Scan error: ${err?.message || 'Failed to execute detection.'}`);
    } finally {
      setScanning(false);
    }
  };

  const handleCreateManualLink = async (e: React.FormEvent) => {
    e.preventDefault();
    const targetId = parseInt(targetCaseId.trim(), 10);
    if (isNaN(targetId) || targetId <= 0) {
      setModalError('Please enter a valid numeric target Case ID.');
      return;
    }
    if (targetId === caseId) {
      setModalError('Cannot link a case to itself.');
      return;
    }

    setModalLoading(true);
    setModalError(null);
    try {
      const payload: ManualLinkCreatePayload = {
        target_case_id: targetId,
        link_type: linkType,
        notes: linkNotes.trim() || undefined,
      };
      await api.post(`/aicte/overlaps/cases/${caseId}/links`, payload);
      setIsManualModalOpen(false);
      setTargetCaseId('');
      setLinkNotes('');
      await loadLinks();
    } catch (err: any) {
      setModalError(err?.message || 'Failed to establish case relationship.');
    } finally {
      setModalLoading(false);
    }
  };

  const handleDeactivateLink = async (linkId: number) => {
    if (!window.confirm('Are you sure you want to deactivate this administrative link? Case dockets remain independent.')) {
      return;
    }
    try {
      await api.patch(`/aicte/overlaps/links/${linkId}`, { is_active: false });
      await loadLinks();
    } catch (err: any) {
      alert(err?.message || 'Failed to deactivate link.');
    }
  };

  return (
    <div className="p-5 bg-white border border-slate-200/80 rounded-2xl shadow-sm space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100">
        <div>
          <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
            <LinkIcon className="w-4 h-4 text-blue-600" />
            Administrative Relationships & Overlaps
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Cross-bureau linkage without combined official dockets.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleScanOverlaps}
            disabled={scanning}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 text-blue-700 border border-blue-200 rounded-xl hover:bg-blue-100 disabled:opacity-50 text-xs font-semibold transition"
          >
            <Search className={`w-3.5 h-3.5 ${scanning ? 'animate-spin' : ''}`} />
            {scanning ? 'Scanning...' : 'Scan for Overlaps'}
          </button>
          <button
            onClick={() => setIsManualModalOpen(true)}
            className="flex items-center gap-1 px-3 py-1.5 border border-slate-200 text-slate-700 rounded-xl hover:bg-slate-50 text-xs font-medium transition"
          >
            <Plus className="w-3.5 h-3.5" />
            Link Case
          </button>
        </div>
      </div>

      {/* Scan alert message */}
      {scanResult && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-900 flex items-start justify-between">
          <span>{scanResult}</span>
          <button
            onClick={() => setScanResult(null)}
            className="text-blue-500 hover:text-blue-700 ml-2"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Links List */}
      {loading ? (
        <div className="p-4 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          Loading case relationships...
        </div>
      ) : error ? (
        <div className="p-3 text-xs text-rose-600 bg-rose-50 border border-rose-200 rounded-xl">
          {error}
        </div>
      ) : links.length === 0 ? (
        <div className="p-6 text-center text-xs text-slate-400 space-y-1">
          <p>No active administrative relationships linked to this case.</p>
          <p className="text-[11px] text-slate-400">
            Use "Scan for Overlaps" to check for duplicate allegations or link related cases manually.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {links.map((link) => (
            <div
              key={link.id}
              className="p-3 bg-slate-50/70 border border-slate-200 rounded-xl flex items-start justify-between gap-3 text-xs"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                    link.link_type === 'DUPLICATE_OF'
                      ? 'bg-rose-100 text-rose-800'
                      : 'bg-blue-100 text-blue-800'
                  }`}>
                    {link.link_type.replace(/_/g, ' ')}
                  </span>
                  <Link
                    to={`/aicte/cases/${link.linked_case_id}`}
                    className="font-mono font-bold text-blue-600 hover:underline flex items-center gap-1"
                  >
                    {link.linked_case_reference}
                    <ExternalLink className="w-3 h-3" />
                  </Link>
                  {link.linked_case_unit_code && (
                    <span className="px-1.5 py-0.2 bg-white text-slate-700 border border-slate-200 rounded text-[10px] font-medium">
                      {link.linked_case_unit_code}
                    </span>
                  )}
                  <span className="text-[10px] text-slate-400">
                    Status: {link.linked_case_status}
                  </span>
                </div>

                <p className="text-slate-800 font-medium text-xs">
                  {link.linked_case_subject}
                </p>

                {link.notes && (
                  <p className="text-slate-500 italic text-[11px]">
                    "{link.notes}"
                  </p>
                )}

                <p className="text-[10px] text-slate-400">
                  Established: {new Date(link.created_at).toLocaleDateString()} by {link.created_by_name || 'Authorized Officer'}
                </p>
              </div>

              <button
                onClick={() => handleDeactivateLink(link.id)}
                className="text-[11px] text-slate-400 hover:text-rose-600 font-medium transition"
                title="Deactivate relationship"
              >
                Deactivate
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Manual Link Modal */}
      {isManualModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                <LinkIcon className="w-4 h-4 text-blue-600" />
                Link Related Case Docket
              </h3>
              <button
                onClick={() => setIsManualModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {modalError && (
              <div className="mt-3 p-2.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{modalError}</span>
              </div>
            )}

            <form onSubmit={handleCreateManualLink} className="mt-4 space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Target Case ID <span className="text-rose-500">*</span>
                </label>
                <input
                  type="number"
                  value={targetCaseId}
                  onChange={(e) => setTargetCaseId(e.target.value)}
                  placeholder="e.g. 42"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-xs"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Relationship Type <span className="text-rose-500">*</span>
                </label>
                <select
                  value={linkType}
                  onChange={(e) => setLinkType(e.target.value as AICTECaseLinkType)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-xs bg-white"
                >
                  <option value="RELATED_TO">RELATED_TO — Same institution / related proceeding</option>
                  <option value="DUPLICATE_OF">DUPLICATE_OF — Same underlying grievance allegation</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Administrative Notes / Reason
                </label>
                <textarea
                  rows={3}
                  value={linkNotes}
                  onChange={(e) => setLinkNotes(e.target.value)}
                  placeholder="Explain the correlation or jurisdictional coordination note..."
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-xs"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsManualModalOpen(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-600 rounded-xl hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={modalLoading}
                  className="px-5 py-2 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 transition shadow-sm"
                >
                  {modalLoading ? 'Linking...' : 'Establish Link'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
