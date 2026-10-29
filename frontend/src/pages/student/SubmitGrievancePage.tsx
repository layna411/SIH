import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../services/api';
import { Institution, GrievanceCategory, AIAnalysisResult, GrievancePriority } from '../../types';
import { 
  Sparkles, 
  Send, 
  UploadCloud, 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle, 
  HelpCircle,
  FileText,
  Lock,
  ArrowRight
} from 'lucide-react';

export const SubmitGrievancePage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [categories, setCategories] = useState<GrievanceCategory[]>([]);
  const [institutionId, setInstitutionId] = useState<number | ''>('');
  const [categoryId, setCategoryId] = useState<number | ''>('');
  const [subcategory, setSubcategory] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<GrievancePriority>('NORMAL');
  const [isConfidential, setIsConfidential] = useState(false);
  const [preferredContact, setPreferredContact] = useState('portal');
  const [files, setFiles] = useState<File[]>([]);

  // AI live analysis state
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [aiResult, setAiResult] = useState<AIAnalysisResult | null>(null);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initial fetch for institutions and categories
  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const [instList, catList] = await Promise.all([
          api.get<Institution[]>('/institutions'),
          api.get<GrievanceCategory[]>('/categories')
        ]);
        setInstitutions(instList);
        setCategories(catList);

        // Pre-select student's associated institution if available
        if (user?.memberships && user.memberships.length > 0) {
          setInstitutionId(user.memberships[0].institution_id);
        } else if (instList.length > 0) {
          setInstitutionId(instList[0].id);
        }

        if (catList.length > 0) {
          setCategoryId(catList[0].id);
        }
      } catch (err) {
        console.error('Error fetching submission metadata', err);
      }
    };
    fetchMetadata();
  }, [user]);

  // Debounced AI live analysis when title or description changes
  useEffect(() => {
    if (title.trim().length < 5 || description.trim().length < 15) {
      setAiResult(null);
      return;
    }

    const timer = setTimeout(async () => {
      setIsAnalyzing(true);
      try {
        const result = await api.post<AIAnalysisResult>('/ai/analyze', {
          title,
          description,
          institution_id: institutionId ? Number(institutionId) : undefined,
          category_id: categoryId ? Number(categoryId) : undefined,
        });
        setAiResult(result);

        // Auto-adopt AI priority if user hasn't explicitly customized it
        if (result.priority && result.priority.priority) {
          setPriority(result.priority.priority);
        }
      } catch (err) {
        console.warn('AI live assistant paused', err);
      } finally {
        setIsAnalyzing(false);
      }
    }, 600);

    return () => clearTimeout(timer);
  }, [title, description, institutionId, categoryId]);

  const handleAdoptAICategory = (catId: number) => {
    setCategoryId(catId);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selected = Array.from(e.target.files);
      setFiles((prev) => [...prev, ...selected]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!institutionId || !categoryId) {
      setError('Please select your institution and an applicable grievance category.');
      return;
    }

    if (title.trim().length < 5) {
      setError('Please enter a clear title (at least 5 characters).');
      return;
    }

    if (description.trim().length < 20) {
      setError('Please provide sufficient description details (at least 20 characters).');
      return;
    }

    setSubmitting(true);
    try {
      const grievance = await api.post<any>('/grievances', {
        institution_id: Number(institutionId),
        category_id: Number(categoryId),
        subcategory: subcategory.trim() || undefined,
        title: title.trim(),
        description: description.trim(),
        priority: priority,
        is_confidential: isConfidential,
        preferred_contact: preferredContact,
      });

      // Upload any attachments
      if (files.length > 0 && grievance.id) {
        for (const f of files) {
          const formData = new FormData();
          formData.append('file', f);
          formData.append('is_internal_only', 'false');
          try {
            await api.post(`/grievances/${grievance.id}/attachments`, formData);
          } catch (attErr) {
            console.error('Attachment upload warning', attErr);
          }
        }
      }

      navigate(`/student/grievances/${grievance.id}?submitted=true`);
    } catch (err: any) {
      setError(err.message || 'Failed to submit grievance. Please verify all fields.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-slate-200/80 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Submit a Grievance</h1>
          <p className="text-xs text-slate-500 mt-1">
            Official complaint registration with automated AI triage and SLA tracking
          </p>
        </div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 text-slate-600 text-xs font-medium">
          <Lock className="w-3.5 h-3.5 text-slate-500" />
          End-to-End Encrypted Session
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Grievance Form */}
        <div className="lg:col-span-2 bg-white p-6 sm:p-8 rounded-2xl border border-slate-200/80 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Institution / University *
                </label>
                <select
                  required
                  value={institutionId}
                  onChange={(e) => setInstitutionId(Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs font-medium bg-white"
                >
                  {institutions.map((inst) => (
                    <option key={inst.id} value={inst.id}>
                      {inst.name} ({inst.code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Category *
                </label>
                <select
                  required
                  value={categoryId}
                  onChange={(e) => setCategoryId(Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs font-medium bg-white"
                >
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name} ({cat.default_sla_days} Days SLA)
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Subcategory / Department (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. Computer Science Dept, Exam Cell, Hostel Warden"
                value={subcategory}
                onChange={(e) => setSubcategory(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Grievance Title *
              </label>
              <input
                type="text"
                required
                placeholder="Concise summary of your grievance..."
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-medium"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Detailed Description *
              </label>
              <textarea
                rows={6}
                required
                placeholder="Please describe the incident or issue clearly, including dates, names of courses/rooms involved, and past steps taken..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs leading-relaxed"
              ></textarea>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Priority
                </label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as GrievancePriority)}
                  className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs bg-white"
                >
                  <option value="LOW">Low (General Feedback)</option>
                  <option value="NORMAL">Normal (Standard Query)</option>
                  <option value="HIGH">High (Impending Deadline)</option>
                  <option value="URGENT">Urgent (Safety / Harassment / Emergency)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Preferred Contact
                </label>
                <select
                  value={preferredContact}
                  onChange={(e) => setPreferredContact(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs bg-white"
                >
                  <option value="portal">In-Portal Messaging (Recommended)</option>
                  <option value="email">Institutional Email</option>
                  <option value="phone">Phone Call</option>
                </select>
              </div>
            </div>

            {/* Supporting Attachments */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Attach Supporting Evidence (Optional)
              </label>
              <div className="border border-dashed border-slate-300 rounded-xl p-4 text-center hover:bg-slate-50 transition cursor-pointer relative">
                <input
                  type="file"
                  multiple
                  accept=".pdf,.png,.jpg,.jpeg,.docx,.txt"
                  onChange={handleFileChange}
                  className="absolute inset-0 opacity-0 cursor-pointer"
                />
                <UploadCloud className="w-6 h-6 text-slate-400 mx-auto mb-1.5" />
                <p className="text-xs font-medium text-slate-700">Click to upload documents</p>
                <p className="text-[10px] text-slate-400 mt-0.5">PDF, PNG, JPG, DOCX up to 10MB each</p>
              </div>

              {files.length > 0 && (
                <div className="mt-2 space-y-1">
                  {files.map((f, i) => (
                    <div key={i} className="flex items-center justify-between text-xs bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
                      <span className="truncate max-w-xs text-slate-700">{f.name}</span>
                      <span className="text-[10px] text-slate-400">{(f.size / 1024).toFixed(0)} KB</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Confidentiality Toggle */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-start gap-3">
              <input
                type="checkbox"
                id="confidentialCheck"
                checked={isConfidential}
                onChange={(e) => setIsConfidential(e.target.checked)}
                className="mt-1 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="confidentialCheck" className="text-xs text-slate-600 leading-relaxed cursor-pointer">
                <span className="font-semibold text-slate-800 block mb-0.5">
                  Enable Confidential Reporting Mode
                </span>
                Mask your identity from departmental dashboards. Your name and roll number will only be visible to the designated inquiry officer.
              </label>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3.5 px-6 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm transition shadow-sm flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {submitting ? 'Registering Grievance...' : 'Submit Grievance'}
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>

        {/* Live AI Assistant Sidebar */}
        <div className="space-y-4">
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50/60 p-5 rounded-2xl border border-blue-200 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center shadow-sm">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-xs">AI Triage Assistant</h3>
                  <p className="text-[10px] text-slate-500">Live NLP guidance</p>
                </div>
              </div>
              {isAnalyzing && (
                <span className="text-[10px] text-blue-600 font-semibold animate-pulse">
                  Analyzing draft...
                </span>
              )}
            </div>

            {aiResult ? (
              <div className="space-y-3.5 text-xs">
                {/* Category Suggestion */}
                <div className="bg-white p-3.5 rounded-xl border border-blue-100 shadow-xs">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                    Suggested Category
                  </span>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900">{aiResult.category.category_name}</span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {Math.round(aiResult.category.confidence * 100)}% match
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
                    {aiResult.category.explanation}
                  </p>
                  {Number(categoryId) !== aiResult.category.category_id && (
                    <button
                      type="button"
                      onClick={() => handleAdoptAICategory(aiResult.category.category_id)}
                      className="mt-2 text-[11px] font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1"
                    >
                      Use this category <ArrowRight className="w-3 h-3" />
                    </button>
                  )}
                </div>

                {/* Priority Suggestion */}
                <div className="bg-white p-3.5 rounded-xl border border-blue-100 shadow-xs">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                    Recommended Priority
                  </span>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900">{aiResult.priority.priority}</span>
                    <span className="text-[11px] text-slate-400">
                      {Math.round(aiResult.priority.confidence * 100)}% weight
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">
                    {aiResult.priority.explanation}
                  </p>
                </div>

                {/* Duplicate Warning */}
                {aiResult.duplicate_check?.is_duplicate_suspected && (
                  <div className="bg-amber-50 p-3.5 rounded-xl border border-amber-200 text-amber-900">
                    <div className="flex items-center gap-1.5 font-bold text-xs mb-1">
                      <AlertTriangle className="w-4 h-4 text-amber-600" />
                      Possible Duplicate Complaint Detected
                    </div>
                    <p className="text-[11px] text-amber-800 leading-relaxed">
                      A similar case (#{aiResult.duplicate_check.matches[0]?.reference_number}) exists in your college with {Math.round((aiResult.duplicate_check.matches[0]?.similarity_score || 0) * 100)}% text similarity.
                    </p>
                  </div>
                )}

                <div className="text-[10px] text-slate-400 pt-1 border-t border-blue-100">
                  Model: {aiResult.category.model_version} • Human officers verify all classifications.
                </div>
              </div>
            ) : (
              <div className="text-center py-6 px-2 text-slate-400 text-xs">
                <FileText className="w-6 h-6 mx-auto mb-2 text-slate-300" />
                <p>Start typing your title and description to receive real-time AI category and priority suggestions.</p>
              </div>
            )}
          </div>

          {/* Privacy Note */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 text-xs text-slate-500 leading-relaxed">
            <h4 className="font-semibold text-slate-800 mb-1 flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4 text-blue-600" />
              Institutional Fair Treatment Policy
            </h4>
            EduResolve AI strictly enforces non-retaliation policies. Submitting a legitimate complaint will not adversely affect your academic standing or grades.
          </div>
        </div>
      </div>
    </div>
  );
};
