import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../services/api';
import { Grievance, GrievanceMessageItem } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { PriorityBadge } from '../../components/common/PriorityBadge';
import { Modal } from '../../components/common/Modal';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { 
  Clock, 
  User, 
  Building2, 
  FileText, 
  Download, 
  Send, 
  CheckCircle2, 
  Star, 
  AlertTriangle,
  ArrowLeft,
  Sparkles,
  Lock,
  MessageSquare,
  ShieldCheck,
  RefreshCw,
  RotateCcw
} from 'lucide-react';

export const GrievanceDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();

  const [grievance, setGrievance] = useState<Grievance | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New message state
  const [messageText, setMessageText] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);

  // Feedback form state
  const [rating, setRating] = useState(5);
  const [satisfiesResolution, setSatisfiesResolution] = useState(true);
  const [feedbackComments, setFeedbackComments] = useState('');
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [feedbackSuccess, setFeedbackSuccess] = useState(false);

  // Reopen request state
  const [isReopenModalOpen, setIsReopenModalOpen] = useState(false);
  const [reopenReason, setReopenReason] = useState('');
  const [submittingReopen, setSubmittingReopen] = useState(false);
  const [downloadingAttId, setDownloadingAttId] = useState<number | null>(null);

  const fetchGrievance = async () => {
    try {
      setLoading(true);
      const data = await api.get<Grievance>(`/grievances/${id}`);
      setGrievance(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load grievance details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      fetchGrievance();
    }
  }, [id]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!messageText.trim() || !grievance) return;

    setSendingMessage(true);
    try {
      const newMsg = await api.post<GrievanceMessageItem>(`/grievances/${grievance.id}/messages`, {
        message: messageText.trim(),
      });
      setGrievance((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          messages: [...(prev.messages || []), newMsg],
        };
      });
      setMessageText('');
    } catch (err: any) {
      alert(err.message || 'Failed to send message.');
    } finally {
      setSendingMessage(false);
    }
  };

  const handleSubmitFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!grievance) return;

    setSubmittingFeedback(true);
    try {
      const fb = await api.post<any>(`/grievances/${grievance.id}/feedback`, {
        rating,
        satisfies_resolution: satisfiesResolution,
        comments: feedbackComments.trim() || undefined,
      });
      setGrievance((prev) => (prev ? { ...prev, feedback: fb } : null));
      setFeedbackSuccess(true);
    } catch (err: any) {
      alert(err.message || 'Failed to submit feedback.');
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const handleDownloadAttachment = async (attId: number, fileName: string) => {
    try {
      setDownloadingAttId(attId);
      await api.downloadFile(`/grievances/${grievance?.id}/attachments/${attId}/download`, fileName);
    } catch (err: any) {
      alert(err.message || 'Error downloading file.');
    } finally {
      setDownloadingAttId(null);
    }
  };

  const handleReopenGrievance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!grievance || !reopenReason.trim() || reopenReason.trim().length < 10) {
      alert('Please provide a detailed reason of at least 10 characters.');
      return;
    }

    setSubmittingReopen(true);
    try {
      const updated = await api.post<Grievance>(`/grievances/${grievance.id}/reopen-request`, {
        reason: reopenReason.trim()
      });
      setGrievance(updated);
      setIsReopenModalOpen(false);
      setReopenReason('');
      alert('Case reopening request submitted successfully.');
      await fetchGrievance();
    } catch (err: any) {
      alert(err.message || 'Failed to request reopening.');
    } finally {
      setSubmittingReopen(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Retrieving grievance timeline and records..." />;
  }

  if (error || !grievance) {
    return (
      <div className="max-w-3xl mx-auto py-12 text-center">
        <AlertTriangle className="w-10 h-10 text-rose-500 mx-auto mb-3" />
        <h2 className="text-xl font-bold text-slate-800">Unable to view grievance</h2>
        <p className="text-sm text-slate-500 mt-1">{error || 'Grievance not found or access unauthorized.'}</p>
        <Link
          to="/student"
          className="mt-6 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 text-white text-xs font-semibold"
        >
          <ArrowLeft className="w-4 h-4" /> Return to Dashboard
        </Link>
      </div>
    );
  }

  const isResolvedOrClosed = ['RESOLVED', 'CLOSED', 'RESOLUTION_PROPOSED'].includes(grievance.status);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <Link
          to="/student"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-blue-600 transition"
        >
          <ArrowLeft className="w-4 h-4" /> Back to My Grievances
        </Link>

        <div className="flex items-center gap-2">
          {['RESOLVED', 'CLOSED'].includes(grievance.status) && (
            <button
              onClick={() => setIsReopenModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-amber-300 bg-amber-50 hover:bg-amber-100 text-amber-800 text-xs font-semibold transition shadow-sm"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Request Reopening
            </button>
          )}
          <StatusBadge status={grievance.status} />
          <PriorityBadge priority={grievance.priority} />
        </div>
      </div>

      {/* Case Header Card */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200/80 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start justify-between gap-4 border-b border-slate-100 pb-5">
          <div>
            <div className="flex items-center gap-2.5 mb-2">
              <span className="font-mono text-xs font-bold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-md border border-blue-200">
                #{grievance.reference_number}
              </span>
              <span className="text-xs text-slate-400 font-medium">
                Filed on {new Date(grievance.created_at).toLocaleDateString('en-IN', {
                  day: 'numeric',
                  month: 'short',
                  year: 'numeric'
                })}
              </span>
              {grievance.is_confidential && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">
                  <Lock className="w-3 h-3 text-slate-500" />
                  Confidential
                </span>
              )}
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 leading-snug">
              {grievance.title}
            </h1>
          </div>

          <div className="text-left sm:text-right shrink-0">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-0.5">
              Assigned Officer
            </span>
            <span className="text-xs font-bold text-slate-800">
              {grievance.assigned_officer_name || 'Grievance Redressal Cell'}
            </span>
          </div>
        </div>

        {/* Description Body */}
        <div className="pt-5">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
            Description
          </h3>
          <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-100">
            {grievance.description}
          </p>
        </div>

        {/* Metadata Grid */}
        <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs pt-4 border-t border-slate-100">
          <div>
            <span className="text-slate-400 block mb-0.5">Institution:</span>
            <span className="font-semibold text-slate-800">{grievance.institution_name}</span>
          </div>
          <div>
            <span className="text-slate-400 block mb-0.5">Category:</span>
            <span className="font-semibold text-slate-800">{grievance.category_name}</span>
          </div>
          <div>
            <span className="text-slate-400 block mb-0.5">Target Due Date:</span>
            <span className="font-semibold text-slate-800">
              {grievance.due_date
                ? new Date(grievance.due_date).toLocaleDateString('en-IN', {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric'
                  })
                : 'Standard 7 Days'}
            </span>
          </div>
          <div>
            <span className="text-slate-400 block mb-0.5">Preferred Contact:</span>
            <span className="font-semibold text-slate-800 capitalize">{grievance.preferred_contact}</span>
          </div>
        </div>
      </div>

      {/* AI Triage Assistance Info Box */}
      {grievance.ai_explanation && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50/50 p-5 rounded-2xl border border-blue-200/80 text-xs text-slate-700">
          <div className="flex items-center gap-2 font-bold text-blue-900 mb-1.5">
            <Sparkles className="w-4 h-4 text-blue-600" />
            AI Intake & Triage Assessment
          </div>
          <p className="text-slate-600 leading-relaxed mb-2">{grievance.ai_explanation}</p>
          <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-500 pt-2 border-t border-blue-100">
            <span>Suggested Category: <strong>{grievance.ai_suggested_category_name || grievance.category_name}</strong></span>
            {grievance.ai_confidence && (
              <span>Confidence: <strong>{Math.round(grievance.ai_confidence * 100)}%</strong></span>
            )}
            <span className="text-slate-400 italic">Advisory suggestion verified by institutional officer.</span>
          </div>
        </div>
      )}

      {/* Resolution Summary Banner if Available */}
      {grievance.resolution_summary && (
        <div className="bg-emerald-50 p-6 rounded-2xl border border-emerald-200 text-emerald-900">
          <div className="flex items-center gap-2 font-bold text-sm text-emerald-800 mb-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            Official Resolution Summary
          </div>
          <p className="text-xs text-emerald-800 whitespace-pre-wrap leading-relaxed">
            {grievance.resolution_summary}
          </p>
        </div>
      )}

      {/* Two Column Layout: Conversation & Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Messages Feed */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200/80 shadow-sm flex flex-col h-[520px]">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-blue-600" />
              Official Case Communication
            </h3>
            <span className="text-[11px] text-slate-400">Student & Officer Chat</span>
          </div>

          {/* Messages Scroll Area */}
          <div className="flex-1 p-6 overflow-y-auto space-y-4">
            {(!grievance.messages || grievance.messages.length === 0) ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs text-center py-12">
                <MessageSquare className="w-8 h-8 text-slate-300 mb-2" />
                <p>No messages exchanged yet.</p>
                <p className="text-[11px] text-slate-400 mt-0.5">Use the box below to ask questions or provide clarifications.</p>
              </div>
            ) : (
              grievance.messages.map((m) => {
                const isMe = m.sender_id === user?.id;
                return (
                  <div
                    key={m.id}
                    className={`flex flex-col ${isMe ? 'items-end' : 'items-start'}`}
                  >
                    <div className="flex items-center gap-1.5 mb-1 text-[10px] text-slate-400">
                      <span className="font-semibold text-slate-700">{m.sender_name}</span>
                      <span>({m.sender_role.replace('_', ' ')})</span>
                      <span>•</span>
                      <span>{new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                    <div
                      className={`max-w-md p-3.5 rounded-2xl text-xs leading-relaxed ${
                        isMe
                          ? 'bg-blue-600 text-white rounded-br-none'
                          : 'bg-slate-100 text-slate-800 rounded-bl-none'
                      }`}
                    >
                      {m.message}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Message Input Box */}
          <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-100 bg-slate-50/50 flex items-center gap-2 rounded-b-2xl">
            <input
              type="text"
              placeholder="Type your message or inquiry..."
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            />
            <button
              type="submit"
              disabled={sendingMessage || !messageText.trim()}
              className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-xl transition flex items-center gap-1.5 disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
              Send
            </button>
          </form>
        </div>

        {/* Right Column: Timeline & Attachments */}
        <div className="space-y-6">
          {/* Timeline */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
            <h3 className="font-bold text-slate-900 text-sm mb-4 flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-600" />
              Status Progression History
            </h3>

            <div className="space-y-4 relative before:absolute before:inset-0 before:left-3 before:w-0.5 before:bg-slate-100">
              {grievance.status_history?.map((h) => (
                <div key={h.id} className="relative flex items-start gap-3 pl-6">
                  <div className="absolute left-1.5 top-1 w-3 h-3 rounded-full bg-blue-600 ring-4 ring-white shrink-0"></div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs text-slate-900">
                        {h.to_status.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-0.5">{h.reason}</p>
                    <span className="text-[10px] text-slate-400 mt-1 block">
                      By {h.changed_by_name} • {new Date(h.created_at).toLocaleDateString('en-IN', {
                        day: 'numeric',
                        month: 'short',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Attachments */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
            <h3 className="font-bold text-slate-900 text-sm mb-3 flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-600" />
              Attached Documents ({grievance.attachments?.length || 0})
            </h3>

            {(!grievance.attachments || grievance.attachments.length === 0) ? (
              <p className="text-xs text-slate-400">No documents attached.</p>
            ) : (
              <div className="space-y-2">
                {grievance.attachments.map((att) => (
                  <div
                    key={att.id}
                    className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-100 text-xs"
                  >
                    <div className="truncate max-w-[160px]">
                      <span className="font-semibold text-slate-800 block truncate">{att.file_name}</span>
                      <span className="text-[10px] text-slate-400">{(att.file_size_bytes / 1024).toFixed(0)} KB</span>
                    </div>
                    <button
                      onClick={() => handleDownloadAttachment(att.id, att.file_name)}
                      disabled={downloadingAttId === att.id}
                      className="p-1.5 rounded-lg text-blue-600 hover:bg-blue-50 transition disabled:opacity-50"
                      title="Download document"
                    >
                      {downloadingAttId === att.id ? (
                        <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
                      ) : (
                        <Download className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Student Feedback Form (Rendered after resolution) */}
          {isResolvedOrClosed && (
            <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
              <h3 className="font-bold text-slate-900 text-sm mb-2 flex items-center gap-2">
                <Star className="w-4 h-4 text-amber-500" />
                Resolution Satisfaction Feedback
              </h3>

              {grievance.feedback ? (
                <div className="bg-amber-50/60 p-4 rounded-xl border border-amber-200 text-xs">
                  <div className="flex items-center gap-1 text-amber-600 font-bold mb-1">
                    {[...Array(grievance.feedback.rating)].map((_, i) => (
                      <Star key={i} className="w-4 h-4 fill-amber-500 text-amber-500" />
                    ))}
                    <span className="ml-1 text-slate-700 font-semibold">{grievance.feedback.rating} / 5</span>
                  </div>
                  <p className="text-slate-700 italic mt-1">"{grievance.feedback.comments || 'Satisfied with resolution.'}"</p>
                </div>
              ) : (
                <form onSubmit={handleSubmitFeedback} className="space-y-3 text-xs">
                  <p className="text-slate-500 text-[11px]">
                    Your case has been marked resolved. Please rate your satisfaction to close the loop.
                  </p>
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Rating (1 to 5 Stars)</label>
                    <div className="flex items-center gap-2">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          onClick={() => setRating(star)}
                          className={`p-1.5 rounded-lg border transition ${
                            rating >= star
                              ? 'bg-amber-50 border-amber-300 text-amber-500'
                              : 'bg-slate-50 border-slate-200 text-slate-300'
                          }`}
                        >
                          <Star className={`w-5 h-5 ${rating >= star ? 'fill-amber-500' : ''}`} />
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Comments (Optional)</label>
                    <textarea
                      rows={2}
                      placeholder="Was the resolution satisfactory? Any further notes..."
                      value={feedbackComments}
                      onChange={(e) => setFeedbackComments(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs"
                    ></textarea>
                  </div>

                  <button
                    type="submit"
                    disabled={submittingFeedback}
                    className="w-full py-2 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition"
                  >
                    {submittingFeedback ? 'Submitting...' : 'Submit Satisfaction Rating'}
                  </button>
                </form>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Reopen Request Modal */}
      {grievance && (
        <Modal
          isOpen={isReopenModalOpen}
          onClose={() => setIsReopenModalOpen(false)}
          title={`Request Reopening: #${grievance.reference_number}`}
          maxWidth="md"
        >
          <form onSubmit={handleReopenGrievance} className="space-y-4 text-xs">
            <p className="text-slate-500 text-[11px] leading-relaxed">
              If the resolution provided was incomplete or the reported issue has resurfaced, submit a formal request for review and case reopening.
            </p>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Detailed Reason for Reopening (Min. 10 characters) *
              </label>
              <textarea
                rows={4}
                required
                minLength={10}
                placeholder="Explain why the resolution was incomplete or how the issue persists..."
                value={reopenReason}
                onChange={(e) => setReopenReason(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs"
              ></textarea>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setIsReopenModalOpen(false)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submittingReopen || reopenReason.trim().length < 10}
                className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-semibold transition disabled:opacity-50 flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                {submittingReopen ? 'Submitting...' : 'Confirm Reopen Request'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
