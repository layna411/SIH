import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Heart } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-slate-400 text-sm border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-4 md:col-span-1">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <span className="font-bold text-white text-base">EduResolve AI</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Centralized AI-assisted student grievance redressal and institutional monitoring platform for higher education institutions.
            </p>
            <div className="text-[11px] text-slate-500 bg-slate-800/80 p-2.5 rounded-lg border border-slate-700/50">
              Disclaimer: Independent educational innovation platform. Not officially endorsed by AICTE or government ministries.
            </div>
          </div>

          <div>
            <h4 className="text-xs font-semibold text-white uppercase tracking-wider mb-4">Platform</h4>
            <ul className="space-y-2 text-xs">
              <li><Link to="/how-it-works" className="hover:text-white transition">How It Works</Link></li>
              <li><Link to="/features" className="hover:text-white transition">Key Features</Link></li>
              <li><Link to="/track" className="hover:text-white transition">Track Grievance</Link></li>
              <li><Link to="/login" className="hover:text-white transition">Institutional Login</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-semibold text-white uppercase tracking-wider mb-4">Governance & Privacy</h4>
            <ul className="space-y-2 text-xs">
              <li><Link to="/privacy" className="hover:text-white transition">Confidentiality & Privacy</Link></li>
              <li><Link to="/about" className="hover:text-white transition">About EduResolve</Link></li>
              <li><Link to="/contact" className="hover:text-white transition">Escalation & Helpdesk</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-semibold text-white uppercase tracking-wider mb-4">Security & Integrity</h4>
            <p className="text-xs text-slate-400 mb-3 leading-relaxed">
              Protected by multi-tenant role authorization, Argon2 password cryptography, and audit trails.
            </p>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs border border-slate-700">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              All Systems Operational
            </div>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4 text-xs">
          <p>© {new Date().getFullYear()} EduResolve AI Platform. All rights reserved.</p>
          <p className="flex items-center gap-1 text-slate-500">
            Engineered for fair and transparent institutional education
          </p>
        </div>
      </div>
    </footer>
  );
};
