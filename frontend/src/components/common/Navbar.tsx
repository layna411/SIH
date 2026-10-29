import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../services/api';
import { NotificationItem } from '../../types';
import { 
  ShieldCheck, 
  Menu, 
  X, 
  LogOut, 
  User as UserIcon, 
  Search, 
  ChevronDown,
  LayoutDashboard,
  Bell,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Check,
  RefreshCw,
  Mail
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);

  // Notification state
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [notifDropdownOpen, setNotifDropdownOpen] = useState<boolean>(false);
  const [notifLoading, setNotifLoading] = useState<boolean>(false);
  const notifRef = useRef<HTMLDivElement>(null);

  // Verification banner state
  const [bannerDismissed, setBannerDismissed] = useState<boolean>(false);
  const [resendingEmail, setResendingEmail] = useState<boolean>(false);
  const [resendCooldown, setResendCooldown] = useState<number>(0);
  const [resendMsg, setResendMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Cooldown timer
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    if (resendCooldown > 0) {
      timer = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [resendCooldown]);

  // Fetch unread count when user is logged in
  const fetchUnreadCount = async () => {
    if (!isAuthenticated) return;
    try {
      const res = await api.get<{ unread_count: number }>('/notifications/unread-count');
      setUnreadCount(res.unread_count);
    } catch {
      // Ignore background notification fetch errors
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchUnreadCount();
      const interval = setInterval(fetchUnreadCount, 45000); // Poll every 45s
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  // Fetch notifications list when opening dropdown
  const fetchNotifications = async () => {
    if (!isAuthenticated) return;
    setNotifLoading(true);
    try {
      const data = await api.get<NotificationItem[]>('/notifications?limit=15');
      setNotifications(data);
    } catch {
      // Ignore
    } finally {
      setNotifLoading(false);
    }
  };

  const handleToggleNotif = () => {
    if (!notifDropdownOpen) {
      fetchNotifications();
    }
    setNotifDropdownOpen(!notifDropdownOpen);
    setUserDropdownOpen(false);
  };

  // Click outside to close dropdowns
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setNotifDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMarkAsRead = async (id: number, link?: string) => {
    try {
      await api.put(`/notifications/${id}/read`);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
      if (link) {
        setNotifDropdownOpen(false);
        navigate(link);
      }
    } catch {
      // Error handling
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.put('/notifications/read-all');
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch {
      // Error handling
    }
  };

  const handleResendVerification = async () => {
    if (resendCooldown > 0 || !user?.email) return;
    setResendingEmail(true);
    setResendMsg(null);
    try {
      const res = await api.post<{ status: string; message: string }>('/auth/resend-verification', {
        email: user.email
      });
      setResendMsg({ type: 'success', text: res.message || 'Verification link sent to your email.' });
      setResendCooldown(60);
    } catch (err: any) {
      setResendMsg({ type: 'error', text: err.message || 'Unable to resend verification email.' });
    } finally {
      setResendingEmail(false);
    }
  };

  const getDashboardPath = () => {
    if (!user) return '/login';
    switch (user.default_role) {
      case 'SUPER_ADMIN':
        return '/admin';
      case 'REGULATORY_ADMIN':
        return '/regulatory';
      case 'INSTITUTION_HEAD':
        return '/head';
      case 'COLLEGE_OFFICER':
        return '/officer';
      case 'STUDENT':
      default:
        return '/student';
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const showVerificationBanner = isAuthenticated && 
    user && 
    user.default_role === 'STUDENT' && 
    user.is_email_verified === false && 
    !bannerDismissed;

  return (
    <>
      {/* Email Verification Alert Banner */}
      {showVerificationBanner && (
        <div className="bg-amber-500/10 border-b border-amber-300 text-amber-900 px-4 py-2.5 text-xs sm:text-sm font-medium transition duration-200">
          <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
              <span>
                <strong>Email not verified:</strong> Please verify <strong>{user?.email}</strong> to ensure you receive real-time case updates.
              </span>
            </div>

            <div className="flex items-center gap-3">
              {resendMsg && (
                <span className={`text-xs ${resendMsg.type === 'success' ? 'text-emerald-700 font-semibold' : 'text-rose-700'}`}>
                  {resendMsg.text}
                </span>
              )}

              <button
                onClick={handleResendVerification}
                disabled={resendingEmail || resendCooldown > 0}
                className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-600 hover:bg-amber-700 disabled:bg-slate-300 text-white rounded-lg text-xs font-medium shadow-sm transition"
              >
                {resendingEmail ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Mail className="w-3.5 h-3.5" />
                )}
                {resendCooldown > 0 ? `Resend (${resendCooldown}s)` : 'Resend Email'}
              </button>

              <button
                onClick={() => setBannerDismissed(true)}
                className="p-1 hover:bg-amber-200/50 rounded text-amber-700"
                title="Dismiss banner"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Navbar */}
      <nav className="bg-white/90 backdrop-blur-md sticky top-0 z-40 border-b border-slate-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center gap-8">
              <Link to="/" className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-md shadow-blue-500/20">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div className="flex flex-col">
                  <span className="font-bold text-lg text-slate-900 leading-tight">
                    EduResolve <span className="text-blue-600">AI</span>
                  </span>
                  <span className="text-[10px] text-slate-500 font-medium tracking-wide uppercase">
                    Centralized Redressal
                  </span>
                </div>
              </Link>

              <div className="hidden md:flex items-center gap-6">
                <Link to="/how-it-works" className="text-sm font-medium text-slate-600 hover:text-blue-600 transition">
                  How It Works
                </Link>
                <Link to="/features" className="text-sm font-medium text-slate-600 hover:text-blue-600 transition">
                  Features
                </Link>
                <Link to="/about" className="text-sm font-medium text-slate-600 hover:text-blue-600 transition">
                  About
                </Link>
                <Link to="/track" className="text-sm font-medium text-slate-600 hover:text-blue-600 flex items-center gap-1.5 transition">
                  <Search className="w-3.5 h-3.5" />
                  Track Grievance
                </Link>
              </div>
            </div>

            <div className="hidden md:flex items-center gap-4">
              {isAuthenticated && user ? (
                <div className="flex items-center gap-3">
                  {/* Notifications Dropdown */}
                  <div className="relative" ref={notifRef}>
                    <button
                      onClick={handleToggleNotif}
                      className="relative p-2 rounded-xl text-slate-600 hover:text-blue-600 hover:bg-slate-100 transition"
                      aria-label="Notifications"
                    >
                      <Bell className="w-5 h-5" />
                      {unreadCount > 0 && (
                        <span className="absolute top-1.5 right-1.5 w-4 h-4 bg-rose-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center ring-2 ring-white">
                          {unreadCount > 9 ? '9+' : unreadCount}
                        </span>
                      )}
                    </button>

                    {notifDropdownOpen && (
                      <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-2xl shadow-2xl border border-slate-100 overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                        <div className="p-3.5 bg-slate-50/80 border-b border-slate-100 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                              Notifications
                            </h3>
                            {unreadCount > 0 && (
                              <span className="bg-blue-100 text-blue-700 text-[10px] font-bold px-2 py-0.5 rounded-full">
                                {unreadCount} new
                              </span>
                            )}
                          </div>
                          {unreadCount > 0 && (
                            <button
                              onClick={handleMarkAllRead}
                              className="text-[11px] font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1 transition"
                            >
                              <Check className="w-3 h-3" /> Mark all read
                            </button>
                          )}
                        </div>

                        <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
                          {notifLoading ? (
                            <div className="p-6 text-center text-xs text-slate-400">
                              <RefreshCw className="w-4 h-4 animate-spin mx-auto mb-2 text-blue-500" />
                              Loading notifications...
                            </div>
                          ) : notifications.length === 0 ? (
                            <div className="p-8 text-center text-xs text-slate-400">
                              <Bell className="w-7 h-7 mx-auto mb-2 text-slate-300" />
                              No notifications yet.
                            </div>
                          ) : (
                            notifications.map((notif) => (
                              <div
                                key={notif.id}
                                onClick={() => handleMarkAsRead(notif.id, notif.link)}
                                className={`p-3.5 transition cursor-pointer hover:bg-slate-50 flex items-start gap-3 ${
                                  !notif.is_read ? 'bg-blue-50/40' : ''
                                }`}
                              >
                                <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${!notif.is_read ? 'bg-blue-600' : 'bg-transparent'}`} />
                                <div className="flex-1 min-w-0">
                                  <p className="text-xs font-semibold text-slate-900 truncate">
                                    {notif.title}
                                  </p>
                                  <p className="text-xs text-slate-600 line-clamp-2 mt-0.5">
                                    {notif.message}
                                  </p>
                                  <div className="flex items-center justify-between mt-1 text-[10px] text-slate-400">
                                    <span>
                                      {new Date(notif.created_at).toLocaleString([], {
                                        month: 'short',
                                        day: 'numeric',
                                        hour: '2-digit',
                                        minute: '2-digit'
                                      })}
                                    </span>
                                    {notif.link && (
                                      <span className="text-blue-600 flex items-center gap-0.5 font-medium">
                                        View <ExternalLink className="w-2.5 h-2.5" />
                                      </span>
                                    )}
                                  </div>
                                </div>
                              </div>
                            ))
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* User Profile Dropdown */}
                  <div className="relative">
                    <button
                      onClick={() => {
                        setUserDropdownOpen(!userDropdownOpen);
                        setNotifDropdownOpen(false);
                      }}
                      className="flex items-center gap-3 py-1.5 px-3 rounded-xl border border-slate-200 hover:border-slate-300 bg-slate-50 transition"
                    >
                      <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-semibold text-xs">
                        {user.full_name?.charAt(0).toUpperCase()}
                      </div>
                      <div className="text-left">
                        <p className="text-xs font-semibold text-slate-800 leading-none">{user.full_name}</p>
                        <p className="text-[10px] text-blue-600 font-medium capitalize mt-0.5">
                          {user.default_role.replace('_', ' ').toLowerCase()}
                        </p>
                      </div>
                      <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                    </button>

                    {userDropdownOpen && (
                      <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-lg border border-slate-100 py-1.5 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                        <div className="px-4 py-2 border-b border-slate-100">
                          <p className="text-xs text-slate-500">Signed in as</p>
                          <p className="text-xs font-medium text-slate-800 truncate">{user.email}</p>
                          {user.is_email_verified ? (
                            <span className="inline-flex items-center gap-1 text-[10px] text-emerald-600 font-medium mt-1">
                              <CheckCircle2 className="w-3 h-3" /> Verified Email
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[10px] text-amber-600 font-medium mt-1">
                              <AlertTriangle className="w-3 h-3" /> Unverified
                            </span>
                          )}
                        </div>

                        <Link
                          to={getDashboardPath()}
                          onClick={() => setUserDropdownOpen(false)}
                          className="flex items-center gap-2 px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
                        >
                          <LayoutDashboard className="w-4 h-4 text-blue-600" />
                          Dashboard
                        </Link>

                        <Link
                          to="/profile"
                          onClick={() => setUserDropdownOpen(false)}
                          className="flex items-center gap-2 px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
                        >
                          <UserIcon className="w-4 h-4 text-slate-400" />
                          Account Settings
                        </Link>

                        <button
                          onClick={handleLogout}
                          className="w-full flex items-center gap-2 px-4 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50 border-t border-slate-100"
                        >
                          <LogOut className="w-4 h-4" />
                          Sign Out
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <Link
                    to="/login"
                    className="px-4 py-2 text-sm font-medium text-slate-700 hover:text-blue-600 transition"
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/register"
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-xl shadow-sm transition shadow-blue-500/10"
                  >
                    Student Register
                  </Link>
                </div>
              )}
            </div>

            <div className="flex md:hidden items-center">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 rounded-lg text-slate-600 hover:bg-slate-100"
              >
                {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-b border-slate-200 bg-white px-4 pt-2 pb-4 space-y-2">
            <Link
              to="/how-it-works"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 rounded-lg"
            >
              How It Works
            </Link>
            <Link
              to="/features"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 rounded-lg"
            >
              Features
            </Link>
            <Link
              to="/track"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 rounded-lg"
            >
              Track Grievance
            </Link>
            <Link
              to="/about"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 rounded-lg"
            >
              About
            </Link>

            <div className="pt-3 border-t border-slate-100">
              {isAuthenticated ? (
                <div className="space-y-1">
                  <Link
                    to={getDashboardPath()}
                    onClick={() => setMobileMenuOpen(false)}
                    className="block w-full text-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg"
                  >
                    Go to Dashboard
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="block w-full text-center px-4 py-2 text-sm font-medium text-rose-600 hover:bg-rose-50 rounded-lg"
                  >
                    Sign Out
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  <Link
                    to="/login"
                    onClick={() => setMobileMenuOpen(false)}
                    className="block w-full text-center px-4 py-2 text-sm font-medium text-slate-700 border border-slate-200 rounded-lg"
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/register"
                    onClick={() => setMobileMenuOpen(false)}
                    className="block w-full text-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg"
                  >
                    Student Register
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}
      </nav>
    </>
  );
};
