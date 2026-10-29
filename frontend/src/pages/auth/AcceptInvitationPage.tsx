import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { api } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { InvitationValidateResponse } from '../../types';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { 
  ShieldCheck, 
  Building2, 
  UserCheck, 
  Lock, 
  Eye, 
  EyeOff, 
  CheckCircle2, 
  AlertCircle, 
  ArrowRight,
  Phone
} from 'lucide-react';

export const AcceptInvitationPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();
  const { setAuthSession } = useAuth();

  const [invitation, setInvitation] = useState<InvitationValidateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [validatingError, setValidatingError] = useState<string | null>(null);

  // Form states
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setValidatingError('No invitation token found in link. Please verify the URL or ask your administrator to resend the invite.');
      setLoading(false);
      return;
    }

    const validate = async () => {
      try {
        setLoading(true);
        const data = await api.get<InvitationValidateResponse>(`/auth/invitations/${token}`);
        setInvitation(data);
      } catch (err: any) {
        setValidatingError(err.message || 'Invitation is invalid, expired, or has already been accepted.');
      } finally {
        setLoading(false);
      }
    };

    validate();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (password.length < 8) {
      setFormError('Password must contain at least 8 characters.');
      return;
    }

    if (password !== confirmPassword) {
      setFormError('Passwords do not match.');
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.post<{ access_token: string; user: any }>(`/auth/invitations/${token}/accept`, {
        password,
        phone_number: phoneNumber.trim() || undefined,
      });

      // Set active session in client
      setAuthSession(res.access_token, res.user);

      // Route to appropriate role portal
      const role = res.user.default_role;
      if (role === 'SUPER_ADMIN') {
        navigate('/admin');
      } else if (role === 'INSTITUTION_HEAD') {
        navigate('/head');
      } else if (role === 'COLLEGE_OFFICER') {
        navigate('/officer');
      } else if (role === 'REGULATORY_ADMIN') {
        navigate('/regulatory');
      } else {
        navigate('/');
      }
    } catch (err: any) {
      setFormError(err.message || 'Failed to activate account. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Verifying secure invitation credentials..." />;
  }

  if (validatingError || !invitation) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full bg-white p-8 rounded-3xl border border-slate-200 shadow-xl text-center space-y-5">
          <div className="w-14 h-14 bg-rose-50 text-rose-600 rounded-2xl flex items-center justify-center mx-auto border border-rose-100">
            <AlertCircle className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Invalid or Expired Invitation</h2>
            <p className="text-xs text-slate-500 mt-2 leading-relaxed">
              {validatingError}
            </p>
          </div>
          <div className="pt-2">
            <Link
              to="/login"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition shadow-sm"
            >
              Go to Login Page <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const roleLabel = invitation.role.replace(/_/g, ' ');

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-6">
        {/* Onboarding Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold">
            <ShieldCheck className="w-3.5 h-3.5" />
            Official Account Invitation
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Activate Your EduResolve Account</h1>
          <p className="text-xs text-slate-500">
            Set your secure password to complete onboarding as an authorized administrator.
          </p>
        </div>

        {/* Invitation Metadata Card */}
        <div className="bg-gradient-to-br from-slate-50 to-blue-50/40 p-5 rounded-2xl border border-blue-100 shadow-xs space-y-3">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200/60">
            <div>
              <p className="text-[11px] text-slate-400 font-medium">Invited User</p>
              <p className="text-sm font-bold text-slate-800">{invitation.full_name}</p>
              <p className="text-xs text-slate-500">{invitation.email}</p>
            </div>
            <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-blue-600 text-white tracking-wide uppercase">
              {roleLabel}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            {invitation.institution_name && (
              <div className="flex items-start gap-1.5 text-slate-600 col-span-2">
                <Building2 className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <div>
                  <span className="text-[10px] text-slate-400 block font-medium">Institution</span>
                  <span className="font-semibold text-slate-800">{invitation.institution_name}</span>
                </div>
              </div>
            )}
            {invitation.department && (
              <div className="text-slate-600">
                <span className="text-[10px] text-slate-400 block font-medium">Department</span>
                <span className="font-medium text-slate-700">{invitation.department}</span>
              </div>
            )}
            {invitation.designation && (
              <div className="text-slate-600">
                <span className="text-[10px] text-slate-400 block font-medium">Designation</span>
                <span className="font-medium text-slate-700">{invitation.designation}</span>
              </div>
            )}
          </div>
        </div>

        {/* Password Setup Form */}
        <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200/80 shadow-lg">
          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            {formError && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                <span>{formError}</span>
              </div>
            )}

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                New Password <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  minLength={8}
                  placeholder="Minimum 8 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Confirm Password <span className="text-rose-500">*</span>
              </label>
              <input
                type={showPassword ? 'text' : 'password'}
                required
                minLength={8}
                placeholder="Re-enter your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Phone Number <span className="text-slate-400 font-normal">(Optional)</span>
              </label>
              <div className="relative">
                <input
                  type="tel"
                  placeholder="+91 9876543210"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  className="w-full pl-9 pr-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <Phone className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              </div>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition shadow-sm flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {submitting ? 'Activating Credentials...' : 'Activate Account & Access Portal'}
                <CheckCircle2 className="w-4 h-4" />
              </button>
            </div>
          </form>

          <div className="mt-4 pt-4 border-t border-slate-100 text-center text-slate-400 text-[11px]">
            Already activated? <Link to="/login" className="text-blue-600 font-semibold hover:underline">Sign In</Link>
          </div>
        </div>
      </div>
    </div>
  );
};
