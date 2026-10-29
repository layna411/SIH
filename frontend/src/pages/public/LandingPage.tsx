import React from 'react';
import { Link } from 'react-router-dom';
import { 
  ShieldCheck, 
  Sparkles, 
  Search, 
  ArrowRight, 
  Clock, 
  Lock, 
  CheckCircle2, 
  Layers, 
  Building2,
  FileText,
  AlertCircle
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="bg-slate-50">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-20 lg:pt-20 lg:pb-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold mb-6 shadow-sm">
              <Sparkles className="w-3.5 h-3.5 text-blue-600 animate-pulse" />
              AI-Powered Centralized Grievance Redressal
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight leading-tight">
              Fair, Transparent & <span className="text-blue-600">Accountable</span> Student Redressal
            </h1>

            <p className="mt-6 text-base sm:text-lg text-slate-600 leading-relaxed">
              EduResolve AI connects students, college grievance officers, and higher education regulatory administrators in a single, secure, multi-institutional platform equipped with intelligent triage assistance.
            </p>

            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/student/submit"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm shadow-md shadow-blue-500/20 transition-all hover:scale-[1.02]"
              >
                Submit a Grievance
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/track"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-white hover:bg-slate-100 text-slate-800 font-semibold text-sm border border-slate-200 shadow-sm transition"
              >
                <Search className="w-4 h-4 text-slate-500" />
                Track by Reference ID
              </Link>
              <Link
                to="/login"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-sm transition"
              >
                Institutional Sign In
              </Link>
            </div>

            <div className="mt-6 text-xs text-slate-400">
              * Independent higher education platform. Regulatory jurisdictions configurable to institutional needs.
            </div>
          </div>
        </div>
      </section>

      {/* Trust & Architecture Metrics */}
      <section className="border-y border-slate-200/80 bg-white py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
              <p className="text-2xl sm:text-3xl font-extrabold text-blue-600">100%</p>
              <p className="text-xs font-medium text-slate-500 mt-1">Audit Trail Transparency</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
              <p className="text-2xl sm:text-3xl font-extrabold text-emerald-600">&lt; 48 Hrs</p>
              <p className="text-xs font-medium text-slate-500 mt-1">Average Officer Intake</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
              <p className="text-2xl sm:text-3xl font-extrabold text-indigo-600">Multi-Tenant</p>
              <p className="text-xs font-medium text-slate-500 mt-1">Strict Institution Isolation</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
              <p className="text-2xl sm:text-3xl font-extrabold text-slate-900">Zero Bias</p>
              <p className="text-xs font-medium text-slate-500 mt-1">Human-in-the-Loop Triage</p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-xs font-bold text-blue-600 uppercase tracking-widest mb-2">Redressal Lifecycle</h2>
          <p className="text-3xl font-extrabold text-slate-900">How EduResolve AI Resolves Concerns</p>
          <p className="mt-3 text-sm text-slate-500">
            A transparent 4-stage pipeline from grievance registration to student satisfaction review.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative">
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm relative">
            <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-sm mb-4">
              1
            </div>
            <h3 className="font-bold text-slate-900 text-base mb-2">Secure Submission</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Student files a grievance with optional evidence attachments and confidentiality preferences.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm relative">
            <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-sm mb-4">
              2
            </div>
            <h3 className="font-bold text-slate-900 text-base mb-2">AI Triage Assist</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Domain NLP suggests category, detects possible duplicates, and highlights urgency indicators.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm relative">
            <div className="w-10 h-10 rounded-xl bg-purple-100 text-purple-600 flex items-center justify-center font-bold text-sm mb-4">
              3
            </div>
            <h3 className="font-bold text-slate-900 text-base mb-2">Investigation & Action</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Assigned college officer communicates with student, conducts inquiry, and maintains internal notes.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm relative">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold text-sm mb-4">
              4
            </div>
            <h3 className="font-bold text-slate-900 text-base mb-2">Resolution & Feedback</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Detailed resolution is recorded, verified by institution head, and rated by the student.
            </p>
          </div>
        </div>
      </section>

      {/* Grievance Categories Showcase */}
      <section className="py-16 bg-white border-t border-slate-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-xs font-bold text-blue-600 uppercase tracking-widest mb-2">Coverage</h2>
            <p className="text-2xl font-bold text-slate-900">Supported Grievance Domains</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {[
              { title: 'Academics & Teaching', desc: 'Syllabus, attendance, course delivery, grade sheets' },
              { title: 'Examinations & Results', desc: 'Admit cards, evaluation, corrections, backlogs' },
              { title: 'Fees & Refunds', desc: 'Caution deposits, double debits, scholarship adjustments' },
              { title: 'Hostel & Mess', desc: 'Room allotment, hygiene, food quality, maintenance' },
              { title: 'Infrastructure & Labs', desc: 'Campus WiFi, library facilities, computer equipment' },
              { title: 'Administration', desc: 'ID cards, bonafide certificates, transfer documents' },
              { title: 'Anti-Ragging & Misconduct', desc: 'Harassment, safety threats, strict confidential escalation' },
              { title: 'Accessibility Support', desc: 'Ramps, assistive tech, psychological counseling' },
            ].map((cat, i) => (
              <div key={i} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition">
                <h4 className="font-semibold text-xs text-slate-900 mb-1">{cat.title}</h4>
                <p className="text-[11px] text-slate-500">{cat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Banner */}
      <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-r from-blue-700 to-indigo-800 rounded-3xl p-8 sm:p-12 text-white text-center shadow-xl shadow-blue-900/10">
          <h2 className="text-2xl sm:text-3xl font-extrabold mb-4">Have an unresolved institutional concern?</h2>
          <p className="text-sm sm:text-base text-blue-100 max-w-xl mx-auto mb-8">
            Submit your grievance in minutes. Track real-time progress with public reference tokens and full status history.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/register"
              className="px-6 py-3 rounded-xl bg-white text-blue-700 font-semibold text-sm hover:bg-blue-50 transition"
            >
              Register as Student
            </Link>
            <Link
              to="/login"
              className="px-6 py-3 rounded-xl bg-blue-900/60 border border-blue-400/30 text-white font-semibold text-sm hover:bg-blue-900 transition"
            >
              Sign In to Portal
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};
