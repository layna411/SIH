import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { 
  ShieldCheck, 
  Lock, 
  Mail, 
  ArrowRight, 
  AlertCircle, 
  Key, 
  Check, 
  Sparkles,
  Users
} from 'lucide-react';

interface DemoAccount {
  role: string;
  label: string;
  email: string;
  password: string;
  badgeClass: string;
  description: string;
}

const DEMO_ACCOUNTS: DemoAccount[] = [
  {
    role: 'SUPER_ADMIN',
    label: 'Super Admin',
    email: 'admin@eduresolve.ai',
    password: 'Password@123',
    badgeClass: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    description: 'AICTE Headquarters & National System Admin',
  },
  {
    role: 'BUREAU_HEAD_RB',
    label: 'Bureau Head (RB)',
    email: 'bureau.rb@aicte.gov.in',
    password: 'Password@123',
    badgeClass: 'bg-rose-50 text-rose-700 border-rose-200',
    description: 'Regulation Bureau (RB) — Case assignment & oversight',
  },
  {
    role: 'BUREAU_OFFICER_PGRC',
    label: 'Bureau Officer (PGRC)',
    email: 'bureau.pgrc@aicte.gov.in',
    password: 'Password@123',
    badgeClass: 'bg-cyan-50 text-cyan-700 border-cyan-200',
    description: 'Public Grievance Redressal Cell — Transfers & resolution',
  },
  {
    role: 'BUREAU_OFFICER_AB',
    label: 'Bureau Officer (AB)',
    email: 'bureau.ab@aicte.gov.in',
    password: 'Password@123',
    badgeClass: 'bg-teal-50 text-teal-700 border-teal-200',
    description: 'Approval Bureau — Approval scrutiny & overlap review',
  },
  {
    role: 'REGULATORY_ADMIN',
    label: 'Regulatory Admin',
    email: 'regulator@education.gov.in',
    password: 'Password@123',
    badgeClass: 'bg-blue-50 text-blue-700 border-blue-200',
    description: 'Regional Office & Bureau Jurisdictional Officer',
  },
  {
    role: 'REGIONAL_OFFICER_NORTH',
    label: 'Regional Officer (North)',
    email: 'ro.north@aicte.gov.in',
    password: 'Password@123',
    badgeClass: 'bg-violet-50 text-violet-700 border-violet-200',
    description: 'AICTE Regional Office (North) Operations',
  },
  {
    role: 'INSTITUTION_HEAD',
    label: 'Institution Head',
    email: 'head@nitdelhi.ac.in',
    password: 'Password@123',
    badgeClass: 'bg-purple-50 text-purple-700 border-purple-200',
    description: 'Director / Principal / Vice-Chancellor',
  },
  {
    role: 'COLLEGE_OFFICER',
    label: 'College Officer',
    email: 'officer@nitdelhi.ac.in',
    password: 'Password@123',
    badgeClass: 'bg-amber-50 text-amber-700 border-amber-200',
    description: 'Campus Grievance Redressal Cell Officer',
  },
  {
    role: 'STUDENT',
    label: 'Student',
    email: 'student@nitdelhi.ac.in',
    password: 'Password@123',
    badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    description: 'Enrolled Student at Verified Institution',
  },
];

export const LoginPage: React.FC = () => {
  const { login, isLoading } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [selectedDemoRole, setSelectedDemoRole] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      const loggedUser = await login(email, password);
      // If user has an active bureau membership and is not a student, direct to AICTE portal
      if (loggedUser.bureau_memberships && loggedUser.bureau_memberships.some((bm) => bm.is_active)) {
        navigate('/aicte');
        return;
      }

      // Navigate to appropriate dashboard based on user role
      switch (loggedUser.default_role) {
        case 'SUPER_ADMIN':
          navigate('/admin');
          break;
        case 'REGULATORY_ADMIN':
          navigate('/regulatory');
          break;
        case 'INSTITUTION_HEAD':
          navigate('/head');
          break;
        case 'COLLEGE_OFFICER':
          navigate('/officer');
          break;
        case 'STUDENT':
        default:
          navigate('/student');
          break;
      }
    } catch (err: any) {
      setError(err.message || 'Incorrect email or password.');
    }
  };

  const handleSelectDemo = (account: DemoAccount) => {
    setEmail(account.email);
    setPassword(account.password);
    setSelectedDemoRole(account.role);
    setError(null);
  };

  return (
    <div className="min-h-[calc(100vh-10rem)] flex flex-col justify-center py-10 px-4 sm:px-6 lg:px-8 bg-slate-50">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="w-12 h-12 rounded-2xl bg-blue-600 text-white flex items-center justify-center mx-auto shadow-md shadow-blue-500/20 mb-3">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Sign in to EduResolve AI</h2>
        <p className="mt-1.5 text-xs text-slate-500">
          Centralized student grievance and institutional monitoring portal
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-lg">
        {/* Main Login Card */}
        <div className="bg-white py-8 px-6 shadow-sm border border-slate-200/80 rounded-2xl sm:px-10">
          {error && (
            <div className="mb-6 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  required
                  placeholder="name@institution.edu"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    setSelectedDemoRole(null);
                  }}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setSelectedDemoRole(null);
                  }}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm transition shadow-sm flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isLoading ? 'Verifying Credentials...' : 'Sign In'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Credentials Banner */}
          <div className="mt-8 pt-6 border-t border-slate-100">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                Quick Demo Credentials (1-Click Fill)
              </span>
              <span className="text-[10px] text-slate-400 font-mono">Password: Password@123</span>
            </div>

            <div className="grid grid-cols-1 gap-2">
              {DEMO_ACCOUNTS.map((acc) => {
                const isSelected = selectedDemoRole === acc.role;
                return (
                  <button
                    key={acc.role}
                    type="button"
                    onClick={() => handleSelectDemo(acc)}
                    className={`w-full text-left p-2.5 rounded-xl border transition flex items-center justify-between group ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50/50 shadow-sm'
                        : 'border-slate-200/80 bg-slate-50/60 hover:bg-slate-100/80 hover:border-slate-300'
                    }`}
                  >
                    <div className="min-w-0 pr-2">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${acc.badgeClass}`}>
                          {acc.label}
                        </span>
                        <span className="text-xs font-medium text-slate-700 truncate font-mono">
                          {acc.email}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 truncate mt-0.5">
                        {acc.description}
                      </p>
                    </div>

                    <div className="shrink-0 flex items-center">
                      {isSelected ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-600">
                          <Check className="w-3.5 h-3.5" />
                          Loaded
                        </span>
                      ) : (
                        <span className="text-[11px] text-slate-400 group-hover:text-blue-600 font-medium">
                          Use →
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="mt-6 text-center text-xs text-slate-500">
            Are you a student without an account?{' '}
            <Link to="/register" className="font-semibold text-blue-600 hover:underline">
              Create Student Account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
