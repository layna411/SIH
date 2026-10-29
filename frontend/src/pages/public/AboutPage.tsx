import React from 'react';
import { ShieldCheck, Target, HeartHandshake, Scale, Lock, Eye } from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <div className="text-center mb-12">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900">About EduResolve AI</h1>
        <p className="mt-3 text-base text-slate-600">
          Transforming institutional grievance redressal through transparency, ethical AI, and rigorous multi-tier accountability.
        </p>
      </div>

      <div className="space-y-12">
        <section className="bg-white p-8 rounded-2xl border border-slate-200/80 shadow-sm">
          <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-blue-600" />
            Our Mission
          </h2>
          <p className="text-sm text-slate-600 leading-relaxed">
            EduResolve AI was architected to address systemic bottlenecks in traditional higher education grievance handling. Colleges often struggle with fragmented email complaints, untracked delays, and lack of standard oversight. EduResolve AI provides a centralized institutional platform where students can safely submit complaints, college officers can investigate and resolve them collaboratively, and regulatory bodies can monitor institutional performance benchmarks.
          </p>
        </section>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-4">
              <Scale className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-base mb-2">Neutral & Transparent</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Every status change is permanently audited with a mandatory rationale. Students observe genuine progress without arbitrary closures.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-4">
              <Lock className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-base mb-2">Multi-Tenant Boundary</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Each institution operates in a strictly isolated data partition. Officers can only review complaints belonging to their verified institution.
            </p>
          </div>
        </div>

        <section className="bg-blue-50/50 p-6 rounded-2xl border border-blue-100 text-xs text-slate-600 leading-relaxed">
          <h4 className="font-bold text-blue-900 mb-2 flex items-center gap-1.5">
            <Eye className="w-4 h-4 text-blue-600" />
            Governance Disclosure
          </h4>
          EduResolve AI is an independent software architecture prototype. It is built to support modern regulatory frameworks (such as AICTE, UGC, or State Higher Education Councils) without falsely claiming government endorsement. Jurisdictional parameters are fully configurable by authorized administrators.
        </section>
      </div>
    </div>
  );
};
