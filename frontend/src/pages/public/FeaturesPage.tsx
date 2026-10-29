import React from 'react';
import { 
  Sparkles, 
  CopyCheck, 
  ShieldCheck, 
  Building2, 
  LineChart, 
  History, 
  MessageSquare, 
  FileUp, 
  Compass, 
  Star 
} from 'lucide-react';

export const FeaturesPage: React.FC = () => {
  const features = [
    {
      title: 'AI Category & Priority Triage',
      desc: 'NLP text analysis automatically recommends proper grievance categorization and flags critical urgency markers like safety or exam deadlines.',
      icon: <Sparkles className="w-5 h-5 text-blue-600" />
    },
    {
      title: 'Duplicate Complaint Detection',
      desc: 'TF-IDF semantic similarity scans existing institutional complaints to detect redundant or identical grievances without merging them autonomously.',
      icon: <CopyCheck className="w-5 h-5 text-indigo-600" />
    },
    {
      title: 'Multi-Tenant Data Isolation',
      desc: 'Complete boundary enforcement prevents cross-institution data exposure. Officers only ever access grievances from their own authorized college.',
      icon: <Building2 className="w-5 h-5 text-emerald-600" />
    },
    {
      title: 'Immutable Status Timeline',
      desc: 'Every transition records previous status, new status, actor, timestamp, and a mandatory reason for total institutional accountability.',
      icon: <History className="w-5 h-5 text-purple-600" />
    },
    {
      title: 'Shielded Internal Notes',
      desc: 'Officers collaborate using private case notes strictly hidden from student view, preserving confidential investigation integrity.',
      icon: <ShieldCheck className="w-5 h-5 text-slate-700" />
    },
    {
      title: 'Secure Private Uploads',
      desc: 'Supporting documents are stored in server-side private storage with strict authorization checks on every download attempt.',
      icon: <FileUp className="w-5 h-5 text-teal-600" />
    },
    {
      title: 'Student Resolution Feedback',
      desc: 'Close-the-loop accountability: Students rate outcome satisfaction (1-5 stars) and comment on whether the resolution met their expectations.',
      icon: <Star className="w-5 h-5 text-amber-500" />
    },
    {
      title: 'Regulatory Jurisdiction Benchmarks',
      desc: 'Authorized regional oversight officers compare resolution rates, overdue cases, and category distributions across assigned institutions.',
      icon: <LineChart className="w-5 h-5 text-rose-600" />
    }
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 py-16">
      <div className="text-center max-w-3xl mx-auto mb-16">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900">Comprehensive Platform Capabilities</h1>
        <p className="mt-3 text-base text-slate-600">
          Engineered to satisfy modern higher education governance standards with security, intelligence, and accessibility.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {features.map((f, i) => (
          <div key={i} className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition">
            <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center mb-4">
              {f.icon}
            </div>
            <h3 className="font-bold text-slate-900 text-sm mb-2">{f.title}</h3>
            <p className="text-xs text-slate-500 leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
