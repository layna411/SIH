import React, { useState, useEffect } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { api } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { 
  CheckCircle2, 
  AlertCircle, 
  Mail, 
  ArrowRight, 
  ShieldCheck,
  RefreshCw,
  Loader2
} from 'lucide-react';

export const VerifyEmailPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();
  const { user, refreshUser, isAuthenticated } = useAuth();

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Resend state
  const [resendEmail, setResendEmail] = useState(user?.email || '');
  const [resendLoading, setResendLoading] = useState(false);
  const [resendSuccess, setResendSuccess] = useState<string | null>(null);
  const [resendError, setResendError] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    if (cooldown > 0) {
      timer = setTimeout(() => setCooldown(cooldown - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [cooldown]);

  useEffect(() => {
    if (!token) return;

    const performVerification = async () => {
      setLoading(true);
      setError(null);
      setSuccess(null);
      try {
        const res = await api.post<{ status: string; message: string; email?: string }>('/auth/verify-email', {
          token: token.trim()
        });
        setSuccess(res.message || 'Email successfully verified! Your account has full access.');
        if (isAuthenticated) {
          await refreshUser();
        }
      } catch (err: any) {
        setError(err.message || 'Verification token is invalid or has expired.');
      } finally {
        setLoading(false);
      }
    };

    performVerification();
  }, [token]);

  const handleResend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resendEmail.trim() || cooldown > 0) return;

    setResendLoading(true);
    setResendError(null);
    setResendSuccess(null);

    try {
      const res = await api.post<{ status: string; message: string }>('/auth/resend-verification', {
        email: resendEmail.trim()
      });
      setResendSuccess(res.message || 'Verification link dispatched if account is registered.');
      setCooldown(60);
    } catch (err: any) {
      setResendError(err.message || 'Failed to dispatch verification email. Please try again.');
    } finally {
      setResendLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl border border-slate-100 p-8">
        <div className="text-center mb-6">
          <div className="w-14 h-14 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-sm border border-blue-100">
            <Mail className="w-7 h-7" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900">Email Verification</h2>
          <p className="text-sm text-slate-500 mt-1">
            EduResolve AI Centralized Grievance Redressal
          </p>
        </div>

        {/* Verifying with token */}
        {loading && (
          <div className="text-center py-8">
            <LoadingSpinner message="Validating verification token..." className="py-4" />
            <p className="text-xs text-slate-400 mt-1">Please wait while we verify your account credentials.</p>
          </div>
        )}

        {/* Success message */}
        {success && !loading && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-5 mb-6 text-center">
            <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto mb-2" />
            <h3 className="text-base font-semibold text-emerald-800">Verification Successful</h3>
            <p className="text-xs text-emerald-700 mt-1">{success}</p>

            <div className="mt-5 flex flex-col gap-2">
              {isAuthenticated ? (
                <button
                  onClick={() => navigate(user?.default_role === 'STUDENT' ? '/student' : '/admin')}
                  className="w-full inline-flex justify-center items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm rounded-xl transition shadow-md shadow-emerald-600/20"
                >
                  Go to Dashboard
                  <ArrowRight className="w-4 h-4" />
                </button>
              ) : (
                <Link
                  to="/login"
                  className="w-full inline-flex justify-center items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm rounded-xl transition shadow-md shadow-blue-600/20"
                >
                  Sign In to Your Account
                  <ArrowRight className="w-4 h-4" />
                </Link>
              )}
            </div>
          </div>
        )}

        {/* Error message */}
        {error && !loading && (
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 mb-6 text-left">
            <div className="flex gap-3">
              <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-rose-800">Verification Failed</h4>
                <p className="text-xs text-rose-700 mt-0.5">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Resend Form if no token or token expired */}
        {(!token || error) && !success && !loading && (
          <div className="border-t border-slate-100 pt-6">
            <h3 className="text-sm font-semibold text-slate-800 mb-1">
              Need a new verification link?
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Enter your registered email address and we'll send you a single-use verification link.
            </p>

            {resendSuccess && (
              <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs rounded-lg p-3 mb-4">
                {resendSuccess}
              </div>
            )}

            {resendError && (
              <div className="bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg p-3 mb-4">
                {resendError}
              </div>
            )}

            <form onSubmit={handleResend} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Registered Email Address
                </label>
                <input
                  type="email"
                  required
                  value={resendEmail}
                  onChange={(e) => setResendEmail(e.target.value)}
                  placeholder="student@institution.edu"
                  className="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <button
                type="submit"
                disabled={resendLoading || cooldown > 0}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white font-medium text-sm rounded-xl transition"
              >
                {resendLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4" />
                    {cooldown > 0 ? `Resend available in ${cooldown}s` : 'Resend Verification Email'}
                  </>
                )}
              </button>
            </form>
          </div>
        )}

        <div className="mt-6 pt-4 border-t border-slate-100 flex justify-between items-center text-xs text-slate-500">
          <Link to="/" className="hover:text-blue-600 transition flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5" /> Back to Home
          </Link>
          <Link to="/login" className="hover:text-blue-600 transition">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
};
