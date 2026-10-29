import React from 'react';
import { Link } from 'react-router-dom';
import { Compass, ArrowLeft, Home, Search, HelpCircle } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-[calc(100vh-14rem)] flex items-center justify-center py-16 px-4 sm:px-6 lg:px-8 bg-slate-50">
      <div className="max-w-md w-full text-center space-y-6 bg-white p-8 sm:p-10 rounded-2xl border border-slate-200/80 shadow-sm">
        <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto border border-blue-100 shadow-sm">
          <Compass className="w-8 h-8 animate-pulse" />
        </div>

        <div>
          <span className="text-xs font-bold text-blue-600 uppercase tracking-widest bg-blue-50 px-3 py-1 rounded-full border border-blue-200">
            Error 404
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 mt-3">
            Page Not Found
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-2 leading-relaxed">
            The requested institutional portal page or resource does not exist or may have been relocated.
          </p>
        </div>

        <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            to="/"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition shadow-sm"
          >
            <Home className="w-4 h-4" />
            Back to Home
          </Link>
          <Link
            to="/track"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition"
          >
            <Search className="w-4 h-4" />
            Track Case
          </Link>
        </div>

        <div className="pt-4 border-t border-slate-100 text-[11px] text-slate-400">
          Need help? Visit our{' '}
          <Link to="/contact" className="text-blue-600 hover:underline font-medium">
            support & contact desk
          </Link>
          .
        </div>
      </div>
    </div>
  );
};
