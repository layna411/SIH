import React from 'react';
import { 
  FileEdit, 
  Cpu, 
  Users, 
  CheckCircle, 
  Star, 
  ArrowDown, 
  ShieldCheck,
  Clock
} from 'lucide-react';

export const HowItWorksPage: React.FC = () => {
  const steps = [
    {
      num: '01',
      title: 'Student Submission',
      desc: 'The student selects their verified college and submits a grievance description with optional attachments. The student can designate the grievance as confidential to mask their identity from general views.',
      icon: <FileEdit className="w-5 h-5 text-blue-600" />
    },
    {
      num: '02',
      title: 'AI Triage & Duplicate Screening',
      desc: 'EduResolve NLP analyzes the text to recommend the exact grievance category and priority level. Scikit-learn TF-IDF checks for recurring duplicate complaints within the institution to prevent redundant workload.',
      icon: <Cpu className="w-5 h-5 text-indigo-600" />
    },
    {
      num: '03',
      title: 'Institutional Assignment & Inquiry',
      desc: 'The grievance cell assigns the case to a qualified officer based on departmental routing rules. The officer reviews evidence, adds internal notes, and communicates with the student via official case messages.',
      icon: <Users className="w-5 h-5 text-purple-600" />
    },
    {
      num: '04',
      title: 'Resolution Proposal & Verification',
      desc: 'The officer records the resolution summary and proposed actions. If the due date is exceeded, the system flags the complaint as overdue or automatically escalates it to the Institution Head.',
      icon: <CheckCircle className="w-5 h-5 text-teal-600" />
    },
    {
      num: '05',
      title: 'Student Feedback & Case Closure',
      desc: 'The student rates their satisfaction with the outcome (1 to 5 stars) and confirms resolution. If unsatisfied, the student may request a review or reopen the complaint within permitted policy rules.',
      icon: <Star className="w-5 h-5 text-amber-500" />
    }
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <div className="text-center mb-16">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900">How Grievance Redressal Works</h1>
        <p className="mt-3 text-base text-slate-600">
          A step-by-step transparent pathway ensuring accountability from intake to resolution.
        </p>
      </div>

      <div className="space-y-6">
        {steps.map((s, idx) => (
          <div key={idx} className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex items-start gap-5">
            <div className="w-12 h-12 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-center shrink-0">
              {s.icon}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono font-bold text-blue-600">{s.num}</span>
                <h3 className="font-bold text-slate-900 text-base">{s.title}</h3>
              </div>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">{s.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
